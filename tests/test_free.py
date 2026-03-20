from datetime import datetime, timedelta
from typing import Optional

import pytest

from .lib import (
    AProperties,
    Context,
    CreateSnapshotTransaction,
    DestroySnapshotTransaction,
    Environment,
    Filesystem,
    Host,
    Snap,
    Snapshot,
    SnapshotFormat,
    Subcmd,
    TestConfig,
    TransferIncrementalTransaction,
    TransferInitialTransaction,
    Zpool,
)


_ZPOOL_SRC = "foo"
_ZPOOL_TGT = "bar"
_DT = datetime.now()
_SNAP_A = SnapshotFormat.format_(dt = _DT)
_SNAP_B = SnapshotFormat.format_(dt = _DT + timedelta(seconds = 1))
_SNAP_C = SnapshotFormat.format_(dt = _DT + timedelta(seconds = 2))
_SNAP_D = SnapshotFormat.format_(dt = _DT + timedelta(seconds = 3))


@pytest.mark.parametrize("json", (False, True))
@pytest.mark.parametrize("route", (None, "", "localhost", "remotehost", "remotehost/remotehost"))
@Environment(TestConfig(
    zpools = [
        Zpool(name = _ZPOOL_SRC, aproperties = AProperties.from_defaults(overlap = 1), datasets = [
            Filesystem(
                name = "one",
                aproperties = AProperties.from_defaults(overlap = 1),
                snapshots = [
                    Snapshot(_SNAP_A),
                    Snapshot(_SNAP_B),
                    Snapshot(_SNAP_C),
                ],
            ),
        ]),
        Zpool(name = _ZPOOL_TGT),
    ]
))
def test_free_min(ctx: Context, route: Optional[str], json: bool):
    """
    minimal free test: oldest snapshot is removed from source after sync

    Setup: source has one child dataset with three pre-created snapshots
    [snap_a, snap_b, snap_c] and overlap=1.  Target starts empty.

    Step 1 – initial sync: transfers all three snapshots to the target via one
    TransferInitial and two TransferIncremental transactions.  This establishes
    [snap_a, snap_b, snap_c] as common snapshots with matching ZFS creation
    timestamps on both sides (zfs receive preserves the source creation time).

    Step 2 – free: with overlap=1 and three common snapshots the engine calls
    free_iter(1), which reverses the common-position list [2, 1, 0] and takes
    nth(0) = position 2 (snap_c).  Everything before that position that lives
    on the source is eligible for removal: snap_a and snap_b.  Two
    DestroySnapshot transactions are expected for the child dataset.

    After execution the source child retains only [snap_c] (one overlapping
    snapshot as requested); the target is left completely unchanged and still
    holds all three snapshots.
    """

    src = f"root%{_ZPOOL_SRC:s}"
    tgt = f"root%{_ZPOOL_TGT:s}"
    if route is not None:
        src = f"{route:s}:{src:s}"
        tgt = f"{route:s}:{tgt:s}"
    json_args = ("-j",) if json else tuple()

    # step 1: sync — transfer [snap_a, snap_b, snap_c] from source to target
    res_sync = ctx.abgleich(Subcmd.sync, *json_args, "-y", src, tgt)
    res_sync.assert_exitcode(0)

    sync_transactions = ctx.parse_transactions(res_sync.stdout, json = json)
    assert len(sync_transactions) == 3
    assert isinstance(sync_transactions[0], TransferInitialTransaction)
    assert sync_transactions[0].dataset == "/one"
    assert sync_transactions[0].snapshot == _SNAP_A
    assert isinstance(sync_transactions[1], TransferIncrementalTransaction)
    assert sync_transactions[1].dataset == "/one"
    assert sync_transactions[1].from_snapshot == _SNAP_A
    assert sync_transactions[1].to_snapshot == _SNAP_B
    assert isinstance(sync_transactions[2], TransferIncrementalTransaction)
    assert sync_transactions[2].dataset == "/one"
    assert sync_transactions[2].from_snapshot == _SNAP_B
    assert sync_transactions[2].to_snapshot == _SNAP_C

    ctx.reload()

    # source child must retain only snap_c (exactly one overlapping snapshot)
    src_snaps = list((ctx[Host.localhost][_ZPOOL_SRC] / "one").snapshots)
    assert len(src_snaps) == 3
    assert src_snaps[0].name == _SNAP_A
    assert src_snaps[1].name == _SNAP_B
    assert src_snaps[2].name == _SNAP_C

    # target child must be completely unchanged
    tgt_snaps = list((ctx[Host.localhost][_ZPOOL_TGT] / "one").snapshots)
    assert len(tgt_snaps) == 3
    assert tgt_snaps[0].name == _SNAP_A
    assert tgt_snaps[1].name == _SNAP_B
    assert tgt_snaps[2].name == _SNAP_C

    # step 2: free — removes snap_a from source (overlap=1, three common snaps)
    res_free = ctx.abgleich(Subcmd.free, *json_args, "-y", src, tgt)
    res_free.assert_exitcode(0)

    free_transactions = ctx.parse_transactions(res_free.stdout, json = json)
    assert len(free_transactions) == 2
    assert isinstance(free_transactions[0], DestroySnapshotTransaction)
    assert free_transactions[0].dataset == "/one"
    assert free_transactions[0].snapshot == _SNAP_A
    assert isinstance(free_transactions[1], DestroySnapshotTransaction)
    assert free_transactions[1].dataset == "/one"
    assert free_transactions[1].snapshot == _SNAP_B

    ctx.reload()

    # source child must retain only snap_c (exactly one overlapping snapshot)
    src_snaps = list((ctx[Host.localhost][_ZPOOL_SRC] / "one").snapshots)
    assert len(src_snaps) == 1
    assert src_snaps[0].name == _SNAP_C

    # target child must be completely unchanged
    tgt_snaps = list((ctx[Host.localhost][_ZPOOL_TGT] / "one").snapshots)
    assert len(tgt_snaps) == 3
    assert tgt_snaps[0].name == _SNAP_A
    assert tgt_snaps[1].name == _SNAP_B
    assert tgt_snaps[2].name == _SNAP_C


@pytest.mark.parametrize("json", (False, True))
@pytest.mark.parametrize("route", (None, "", "localhost", "remotehost", "remotehost/remotehost"))
@Environment(TestConfig(
    zpools = [
        Zpool(name = _ZPOOL_SRC, aproperties = AProperties.from_defaults(overlap = 1), datasets = [
            Filesystem(
                name = "one",
                aproperties = AProperties.from_defaults(overlap = 1),
                snapshots = [
                    Snapshot(_SNAP_A),
                ],
            ),
        ]),
        Zpool(name = _ZPOOL_TGT),
    ]
))
def test_free_boundary_no_free(ctx: Context, route: Optional[str], json: bool):
    """
    free produces no transactions when common snapshot count equals overlap

    Setup: source child has exactly one pre-created snapshot and overlap=1.
    After syncing to the target there is exactly one common snapshot [snap_a].

    free_iter(1) reverses the common-position list [0] and takes nth(0) =
    position 0.  sequence[0..0] is empty, so nothing qualifies for removal.
    This is the boundary: n_common == overlap, every common snapshot must be
    retained to satisfy the overlap requirement.

    After the free call the source and target must be completely unchanged.
    """

    src = f"root%{_ZPOOL_SRC:s}"
    tgt = f"root%{_ZPOOL_TGT:s}"
    if route is not None:
        src = f"{route:s}:{src:s}"
        tgt = f"{route:s}:{tgt:s}"
    json_args = ("-j",) if json else tuple()

    # step 1: sync — transfer [snap_a] from source to target
    res_sync = ctx.abgleich(Subcmd.sync, *json_args, "-y", src, tgt)
    res_sync.assert_exitcode(0)

    ctx.reload()

    src_snaps = list((ctx[Host.localhost][_ZPOOL_SRC] / "one").snapshots)
    assert len(src_snaps) == 1
    assert src_snaps[0].name == _SNAP_A

    tgt_snaps = list((ctx[Host.localhost][_ZPOOL_TGT] / "one").snapshots)
    assert len(tgt_snaps) == 1
    assert tgt_snaps[0].name == _SNAP_A

    sync_transactions = ctx.parse_transactions(res_sync.stdout, json = json)
    assert len(sync_transactions) == 1
    assert isinstance(sync_transactions[0], TransferInitialTransaction)
    assert sync_transactions[0].dataset == "/one"
    assert sync_transactions[0].snapshot == _SNAP_A

    # step 2: free — one common snapshot with overlap=1: nothing to free
    res_free = ctx.abgleich(Subcmd.free, *json_args, "-y", src, tgt)
    res_free.assert_exitcode(0)

    free_transactions = ctx.parse_transactions(res_free.stdout, json = json)
    assert len(free_transactions) == 0

    ctx.reload()

    # source child must be completely unchanged
    src_snaps = list((ctx[Host.localhost][_ZPOOL_SRC] / "one").snapshots)
    assert len(src_snaps) == 1
    assert src_snaps[0].name == _SNAP_A

    # target child must also be unchanged
    tgt_snaps = list((ctx[Host.localhost][_ZPOOL_TGT] / "one").snapshots)
    assert len(tgt_snaps) == 1
    assert tgt_snaps[0].name == _SNAP_A


@pytest.mark.parametrize("json", (False, True))
@pytest.mark.parametrize("route", (None, "", "localhost", "remotehost", "remotehost/remotehost"))
@Environment(TestConfig(
    zpools = [
        Zpool(name = _ZPOOL_SRC, datasets = [
            Filesystem(
                name = "one",
                aproperties = AProperties.from_defaults(),
                snapshots = [
                    Snapshot(_SNAP_A),
                    Snapshot(_SNAP_B),
                    Snapshot(_SNAP_C),
                    Snapshot(_SNAP_D),
                ],
            ),
        ]),
        Zpool(name = _ZPOOL_TGT),
    ]
))
def test_free_default_overlap(ctx: Context, route: Optional[str], json: bool):
    """
    free removes one snapshot under the default overlap of two

    Setup: source child has four pre-created snapshots and the default overlap
    of 2 (from AProperties.from_defaults(), which sets abgleich:overlap=2).
    Target starts empty.

    Step 1 – sync: transfers all four snapshots (one TransferInitial and three
    TransferIncremental transactions).

    Step 2 – free: with overlap=2 and four common snapshots free_iter(2)
    reverses the common-position list [3, 2, 1, 0] and takes nth(1) = position
    2 (snap_c).  sequence[0..2] = [snap_a, snap_b], filtered by is_on_source,
    yields two DestroySnapshot transactions for snap_a and snap_b.

    After execution the source child holds [snap_c, snap_d] (exactly two
    overlapping snapshots as requested) while the target retains all four
    snapshots unchanged.
    """

    src = f"root%{_ZPOOL_SRC:s}"
    tgt = f"root%{_ZPOOL_TGT:s}"
    if route is not None:
        src = f"{route:s}:{src:s}"
        tgt = f"{route:s}:{tgt:s}"
    json_args = ("-j",) if json else tuple()

    # step 1: sync — transfer [snap_a, snap_b, snap_c, snap_d] from source to target
    res_sync = ctx.abgleich(Subcmd.sync, *json_args, "-y", src, tgt)
    res_sync.assert_exitcode(0)

    sync_transactions = ctx.parse_transactions(res_sync.stdout, json = json)
    assert len(sync_transactions) == 4
    assert isinstance(sync_transactions[0], TransferInitialTransaction)
    assert sync_transactions[0].dataset == "/one"
    assert sync_transactions[0].snapshot == _SNAP_A
    assert isinstance(sync_transactions[1], TransferIncrementalTransaction)
    assert sync_transactions[1].dataset == "/one"
    assert sync_transactions[1].from_snapshot == _SNAP_A
    assert sync_transactions[1].to_snapshot == _SNAP_B
    assert isinstance(sync_transactions[2], TransferIncrementalTransaction)
    assert sync_transactions[2].dataset == "/one"
    assert sync_transactions[2].from_snapshot == _SNAP_B
    assert sync_transactions[2].to_snapshot == _SNAP_C
    assert isinstance(sync_transactions[3], TransferIncrementalTransaction)
    assert sync_transactions[3].dataset == "/one"
    assert sync_transactions[3].from_snapshot == _SNAP_C
    assert sync_transactions[3].to_snapshot == _SNAP_D

    # step 2: free — overlap=2, four common snapshots: snap_a and snap_b are freed
    res_free = ctx.abgleich(Subcmd.free, *json_args, "-y", src, tgt)
    res_free.assert_exitcode(0)

    free_transactions = ctx.parse_transactions(res_free.stdout, json = json)
    assert len(free_transactions) == 2
    assert isinstance(free_transactions[0], DestroySnapshotTransaction)
    assert free_transactions[0].dataset == "/one"
    assert free_transactions[0].snapshot == _SNAP_A
    assert isinstance(free_transactions[1], DestroySnapshotTransaction)
    assert free_transactions[1].dataset == "/one"
    assert free_transactions[1].snapshot == _SNAP_B

    ctx.reload()

    # source child must retain snap_c and snap_d (exactly two overlapping snapshots)
    src_snaps = list((ctx[Host.localhost][_ZPOOL_SRC] / "one").snapshots)
    assert len(src_snaps) == 2
    assert src_snaps[0].name == _SNAP_C
    assert src_snaps[1].name == _SNAP_D

    # target child must be completely unchanged
    tgt_snaps = list((ctx[Host.localhost][_ZPOOL_TGT] / "one").snapshots)
    assert len(tgt_snaps) == 4
    assert tgt_snaps[0].name == _SNAP_A
    assert tgt_snaps[1].name == _SNAP_B
    assert tgt_snaps[2].name == _SNAP_C
    assert tgt_snaps[3].name == _SNAP_D


@pytest.mark.parametrize("json", (False, True))
@pytest.mark.parametrize("route", (None, "", "localhost", "remotehost", "remotehost/remotehost"))
@Environment(TestConfig(
    zpools = [
        Zpool(name = _ZPOOL_SRC, aproperties = AProperties.from_defaults(overlap = -1), datasets = [
            Filesystem(
                name = "one",
                aproperties = AProperties.from_defaults(overlap = -1),
                snapshots = [
                    Snapshot(_SNAP_A),
                    Snapshot(_SNAP_B),
                    Snapshot(_SNAP_C),
                ],
            ),
        ]),
        Zpool(name = _ZPOOL_TGT),
    ]
))
def test_free_negative_overlap(ctx: Context, route: Optional[str], json: bool):
    """
    overlap=-1 is a keep-all sentinel: free never removes anything

    Setup: source child has three pre-created snapshots and overlap=-1.
    Target starts empty.

    Step 1 – sync: transfers all three snapshots.

    Step 2 – free: free_iter(-1) takes the else branch which hard-codes
    position=0, yielding sequence[0..0] which is always empty regardless of
    how many common snapshots exist.  No snapshots are removed from either
    side.
    """

    src = f"root%{_ZPOOL_SRC:s}"
    tgt = f"root%{_ZPOOL_TGT:s}"
    if route is not None:
        src = f"{route:s}:{src:s}"
        tgt = f"{route:s}:{tgt:s}"
    json_args = ("-j",) if json else tuple()

    # step 1: sync — transfer [snap_a, snap_b, snap_c] from source to target
    res_sync = ctx.abgleich(Subcmd.sync, *json_args, "-y", src, tgt)
    res_sync.assert_exitcode(0)

    ctx.reload()

    src_snaps = list((ctx[Host.localhost][_ZPOOL_SRC] / "one").snapshots)
    assert len(src_snaps) == 3
    assert src_snaps[0].name == _SNAP_A
    assert src_snaps[1].name == _SNAP_B
    assert src_snaps[2].name == _SNAP_C

    tgt_snaps = list((ctx[Host.localhost][_ZPOOL_TGT] / "one").snapshots)
    assert len(tgt_snaps) == 3
    assert tgt_snaps[0].name == _SNAP_A
    assert tgt_snaps[1].name == _SNAP_B
    assert tgt_snaps[2].name == _SNAP_C

    # step 2: free — negative overlap: nothing must be freed
    res_free = ctx.abgleich(Subcmd.free, *json_args, "-y", src, tgt)
    res_free.assert_exitcode(0)

    free_transactions = ctx.parse_transactions(res_free.stdout, json = json)
    assert len(free_transactions) == 0

    ctx.reload()

    # source child must be completely unchanged
    src_snaps = list((ctx[Host.localhost][_ZPOOL_SRC] / "one").snapshots)
    assert len(src_snaps) == 3
    assert src_snaps[0].name == _SNAP_A
    assert src_snaps[1].name == _SNAP_B
    assert src_snaps[2].name == _SNAP_C

    # target child must also be unchanged
    tgt_snaps = list((ctx[Host.localhost][_ZPOOL_TGT] / "one").snapshots)
    assert len(tgt_snaps) == 3
    assert tgt_snaps[0].name == _SNAP_A
    assert tgt_snaps[1].name == _SNAP_B
    assert tgt_snaps[2].name == _SNAP_C


@Environment(TestConfig(
    zpools = [
        Zpool(name = _ZPOOL_SRC, aproperties = AProperties.from_defaults(overlap = 1), datasets = [
            Filesystem(
                name = "one",
                aproperties = AProperties.from_defaults(overlap = 0),
                snapshots = [
                    Snapshot(_SNAP_A),
                    Snapshot(_SNAP_B),
                    Snapshot(_SNAP_C),
                ],
            ),
        ]),
        Zpool(name = _ZPOOL_TGT),
    ]
))
def test_free_overlap_zero_error(ctx: Context):
    """
    overlap=0 is rejected with a non-zero exit code

    free_iter(0) returns Err(OverlapZeroError) immediately, before any
    transaction is produced or executed.  The process must exit with a non-zero
    code and leave both source and target completely unchanged.

    The test performs a sync first so that common snapshots exist; the error
    still occurs because the overlap check happens before any iteration.
    """

    src = f"root%{_ZPOOL_SRC:s}"
    tgt = f"root%{_ZPOOL_TGT:s}"

    # step 1: sync — establish common snapshots
    res_sync = ctx.abgleich(Subcmd.sync, "-y", src, tgt)
    res_sync.assert_exitcode(0)

    # step 2: free — overlap=0 must be rejected
    res_free = ctx.abgleich(Subcmd.free, "-y", src, tgt)
    res_free.assert_exitcode(1)

    ctx.reload()

    # source child must be completely unchanged
    src_snaps = list((ctx[Host.localhost][_ZPOOL_SRC] / "one").snapshots)
    assert len(src_snaps) == 3
    assert src_snaps[0].name == _SNAP_A
    assert src_snaps[1].name == _SNAP_B
    assert src_snaps[2].name == _SNAP_C

    # target child must also be unchanged
    tgt_snaps = list((ctx[Host.localhost][_ZPOOL_TGT] / "one").snapshots)
    assert len(tgt_snaps) == 3
    assert tgt_snaps[0].name == _SNAP_A
    assert tgt_snaps[1].name == _SNAP_B
    assert tgt_snaps[2].name == _SNAP_C


@pytest.mark.parametrize("json", (False, True))
@pytest.mark.parametrize("route", (None, "", "localhost", "remotehost", "remotehost/remotehost"))
@Environment(TestConfig(
    zpools = [
        Zpool(name = _ZPOOL_SRC, aproperties = AProperties.from_defaults(overlap = 1), datasets = [
            Filesystem(
                name = "one",
                aproperties = AProperties.from_defaults(overlap = 1),
                snapshots = [
                    Snapshot(_SNAP_A),
                ],
            ),
        ]),
        Zpool(name = _ZPOOL_TGT, datasets = [
            Filesystem(
                name = "one",
                snapshots = [
                    Snapshot(_SNAP_B),
                ],
            ),
        ]),
    ]
))
def test_free_no_common_snapshots(ctx: Context, route: Optional[str], json: bool):
    """
    free produces no transactions when source and target share no snapshots

    Both source and target carry the same child dataset 'one', but each was
    populated independently: source holds [snap_a] and target holds [snap_b].
    The names differ so the common-snapshot set is empty.

    SequenceBuilder.build() detects common.len()==0 and calls
    from_uncommon_datasets(), which returns a sequence containing only
    source-only and target-only entries.  free_iter() finds no common positions,
    so nth(overlap) returns None and unwrap_or(0) yields position=0, making
    sequence[0..0] empty.  No DestroySnapshot transaction is produced and the
    process exits cleanly.

    No sync step is performed; both datasets are pre-populated via the test
    fixture so their ZFS creation timestamps are independent.
    """

    src = f"root%{_ZPOOL_SRC:s}"
    tgt = f"root%{_ZPOOL_TGT:s}"
    if route is not None:
        src = f"{route:s}:{src:s}"
        tgt = f"{route:s}:{tgt:s}"
    json_args = ("-j",) if json else tuple()

    res_free = ctx.abgleich(Subcmd.free, *json_args, "-y", src, tgt)
    res_free.assert_exitcode(0)

    free_transactions = ctx.parse_transactions(res_free.stdout, json = json)
    assert len(free_transactions) == 0

    ctx.reload()

    # source child must be completely unchanged
    src_snaps = list((ctx[Host.localhost][_ZPOOL_SRC] / "one").snapshots)
    assert len(src_snaps) == 1
    assert src_snaps[0].name == _SNAP_A

    # target child must also be completely unchanged
    tgt_snaps = list((ctx[Host.localhost][_ZPOOL_TGT] / "one").snapshots)
    assert len(tgt_snaps) == 1
    assert tgt_snaps[0].name == _SNAP_B


@pytest.mark.parametrize("json", (False, True))
@pytest.mark.parametrize("route", (None, "", "localhost", "remotehost", "remotehost/remotehost"))
@Environment(TestConfig(
    zpools = [
        Zpool(name = _ZPOOL_SRC, aproperties = AProperties.from_defaults(overlap = 1), datasets = [
            Filesystem(
                name = "one",
                aproperties = AProperties.from_defaults(overlap = 1),
                snapshots = [
                    Snapshot(_SNAP_A),
                    Snapshot(_SNAP_B),
                    Snapshot(_SNAP_C),
                ],
            ),
        ]),
        Zpool(name = _ZPOOL_TGT),  # no 'one' dataset
    ]
))
def test_free_dataset_only_on_source(ctx: Context, route: Optional[str], json: bool):
    """
    free skips datasets that exist only on the source

    DatasetComparison.get_free_transactions() returns an empty TransactionList
    immediately for the (Some, None) case — that is, when the dataset exists on
    the source but not on the target.  No sync is performed so the target never
    receives 'one', causing exactly that pattern.

    The root datasets of both zpools have no snapshots and also produce no
    transactions.  The overall result is 0 transactions and exit 0, with the
    source left completely unchanged.
    """

    src = f"root%{_ZPOOL_SRC:s}"
    tgt = f"root%{_ZPOOL_TGT:s}"
    if route is not None:
        src = f"{route:s}:{src:s}"
        tgt = f"{route:s}:{tgt:s}"
    json_args = ("-j",) if json else tuple()

    res_free = ctx.abgleich(Subcmd.free, *json_args, "-y", src, tgt)
    res_free.assert_exitcode(0)

    free_transactions = ctx.parse_transactions(res_free.stdout, json = json)
    assert len(free_transactions) == 0

    ctx.reload()

    # source child must be completely unchanged
    src_snaps = list((ctx[Host.localhost][_ZPOOL_SRC] / "one").snapshots)
    assert len(src_snaps) == 3
    assert src_snaps[0].name == _SNAP_A
    assert src_snaps[1].name == _SNAP_B
    assert src_snaps[2].name == _SNAP_C


@pytest.mark.parametrize("json", (False, True))
@pytest.mark.parametrize("route", (None, "", "localhost", "remotehost", "remotehost/remotehost"))
@Environment(TestConfig(
    zpools = [
        Zpool(name = _ZPOOL_SRC, aproperties = AProperties.from_defaults(overlap = 1), datasets = [
            Filesystem(
                name = "one",
                aproperties = AProperties.from_defaults(overlap = 1),
                snapshots = [
                    Snapshot(_SNAP_A),
                    Snapshot(_SNAP_B),
                    Snapshot(_SNAP_C),
                ],
            ),
            Filesystem(
                name = "two",
                aproperties = AProperties.from_defaults(overlap = 1),
                snapshots = [
                    Snapshot(_SNAP_A),
                    Snapshot(_SNAP_B),
                ],
            ),
        ]),
        Zpool(name = _ZPOOL_TGT),
    ]
))
def test_free_multiple_datasets(ctx: Context, route: Optional[str], json: bool):
    """
    free governs each child dataset independently

    Source has two child datasets with the same overlap=1:
      'one' carries three pre-created snapshots [snap_a, snap_b, snap_c]
      'two' carries two pre-created snapshots  [snap_a, snap_b]

    After syncing both datasets to the target the common snapshot counts are 3
    and 2 respectively.

    free_iter(1) for 'one': reversed positions [2,1,0], nth(0)=2, sequence[0..2]=
    [snap_a, snap_b] → two DestroySnapshot transactions.

    free_iter(1) for 'two': reversed positions [1,0], nth(0)=1, sequence[0..1]=
    [snap_a] → one DestroySnapshot transaction.

    Datasets are processed in alphabetical order ('one' before 'two'), yielding
    three destroy transactions total.  After execution source 'one' retains
    [snap_c] and source 'two' retains [snap_b].
    """

    src = f"root%{_ZPOOL_SRC:s}"
    tgt = f"root%{_ZPOOL_TGT:s}"
    if route is not None:
        src = f"{route:s}:{src:s}"
        tgt = f"{route:s}:{tgt:s}"
    json_args = ("-j",) if json else tuple()

    # step 1: sync — transfer both datasets from source to target
    res_sync = ctx.abgleich(Subcmd.sync, *json_args, "-y", src, tgt)
    res_sync.assert_exitcode(0)

    sync_transactions = ctx.parse_transactions(res_sync.stdout, json = json)
    assert len(sync_transactions) == 5  # 3 for 'one' + 2 for 'two'

    assert isinstance(sync_transactions[0], TransferInitialTransaction)
    assert sync_transactions[0].dataset == "/one"
    assert sync_transactions[0].snapshot == _SNAP_A
    assert isinstance(sync_transactions[1], TransferIncrementalTransaction)
    assert sync_transactions[1].dataset == "/one"
    assert sync_transactions[1].from_snapshot == _SNAP_A
    assert sync_transactions[1].to_snapshot == _SNAP_B
    assert isinstance(sync_transactions[2], TransferIncrementalTransaction)
    assert sync_transactions[2].dataset == "/one"
    assert sync_transactions[2].from_snapshot == _SNAP_B
    assert sync_transactions[2].to_snapshot == _SNAP_C
    assert isinstance(sync_transactions[3], TransferInitialTransaction)
    assert sync_transactions[3].dataset == "/two"
    assert sync_transactions[3].snapshot == _SNAP_A
    assert isinstance(sync_transactions[4], TransferIncrementalTransaction)
    assert sync_transactions[4].dataset == "/two"
    assert sync_transactions[4].from_snapshot == _SNAP_A
    assert sync_transactions[4].to_snapshot == _SNAP_B

    # step 2: free — 'one' (3 common, overlap=1) frees snap_a+snap_b; 'two' (2 common) frees snap_a
    res_free = ctx.abgleich(Subcmd.free, *json_args, "-y", src, tgt)
    res_free.assert_exitcode(0)

    free_transactions = ctx.parse_transactions(res_free.stdout, json = json)
    assert len(free_transactions) == 3
    assert isinstance(free_transactions[0], DestroySnapshotTransaction)
    assert free_transactions[0].dataset == "/one"
    assert free_transactions[0].snapshot == _SNAP_A
    assert isinstance(free_transactions[1], DestroySnapshotTransaction)
    assert free_transactions[1].dataset == "/one"
    assert free_transactions[1].snapshot == _SNAP_B
    assert isinstance(free_transactions[2], DestroySnapshotTransaction)
    assert free_transactions[2].dataset == "/two"
    assert free_transactions[2].snapshot == _SNAP_A

    ctx.reload()

    # 'one' source: only snap_c remains (one overlapping snapshot)
    one_src = list((ctx[Host.localhost][_ZPOOL_SRC] / "one").snapshots)
    assert len(one_src) == 1
    assert one_src[0].name == _SNAP_C

    # 'one' target: all three unchanged
    one_tgt = list((ctx[Host.localhost][_ZPOOL_TGT] / "one").snapshots)
    assert len(one_tgt) == 3
    assert one_tgt[0].name == _SNAP_A
    assert one_tgt[1].name == _SNAP_B
    assert one_tgt[2].name == _SNAP_C

    # 'two' source: only snap_b remains (one overlapping snapshot)
    two_src = list((ctx[Host.localhost][_ZPOOL_SRC] / "two").snapshots)
    assert len(two_src) == 1
    assert two_src[0].name == _SNAP_B

    # 'two' target: unchanged
    two_tgt = list((ctx[Host.localhost][_ZPOOL_TGT] / "two").snapshots)
    assert len(two_tgt) == 2
    assert two_tgt[0].name == _SNAP_A
    assert two_tgt[1].name == _SNAP_B


@pytest.mark.parametrize("json", (False, True))
@pytest.mark.parametrize("route", (None, "", "localhost", "remotehost", "remotehost/remotehost"))
@Environment(TestConfig(
    zpools = [
        Zpool(
            name = _ZPOOL_SRC,
            aproperties = AProperties.from_defaults(snap = Snap.never, overlap = 1),
            datasets = [
                Filesystem(
                    name = "one",
                    aproperties = AProperties.from_defaults(snap = Snap.always, overlap = 1),
                    snapshots = [
                        Snapshot(_SNAP_A),
                        Snapshot(_SNAP_B),
                        Snapshot(_SNAP_C),
                    ],
                ),
            ],
        ),
        Zpool(name = _ZPOOL_TGT),
    ]
))
def test_free_then_sync(ctx: Context, route: Optional[str], json: bool):
    """
    incremental sync remains functional after free has removed the oldest snapshot

    This is an integration test validating that free does not break the
    bookkeeping required for subsequent incremental transfers.

    Setup: source root has snap=never so only the child dataset is ever
    snapshotted; source child 'one' starts with [snap_a, snap_b, snap_c] and
    overlap=1.  Target starts empty.

    Step 1 – initial sync: establishes [snap_a, snap_b, snap_c] as common
    snapshots on both sides with matching ZFS creation timestamps.

    Step 2 – free: with overlap=1 and three common snapshots, snap_a and
    snap_b are destroyed from source.  Source now holds [snap_c]; target still
    holds [snap_a, snap_b, snap_c].  snap_c is the last (and only remaining)
    common snapshot and serves as the base for future incremental sends.

    Step 3 – snap: creates snap_d on source child via 'abgleich snap'.  Its
    name and exact ZFS creation time are captured from the transaction output.

    Step 4 – incremental sync: the engine builds a sequence from
    source=[snap_c, snap_d] and target=[snap_a, snap_b, snap_c].
    snap_c is the last common snapshot; sync_iter produces (snap_c, snap_d) →
    one TransferIncremental transaction.

    Final state: source=[snap_c, snap_d], target=[snap_a, snap_b, snap_c,
    snap_d].
    """

    src = f"root%{_ZPOOL_SRC:s}"
    tgt = f"root%{_ZPOOL_TGT:s}"
    if route is not None:
        src = f"{route:s}:{src:s}"
        tgt = f"{route:s}:{tgt:s}"
    json_args = ("-j",) if json else tuple()

    # step 1: initial sync
    res_sync1 = ctx.abgleich(Subcmd.sync, *json_args, "-y", src, tgt)
    res_sync1.assert_exitcode(0)

    sync1_transactions = ctx.parse_transactions(res_sync1.stdout, json = json)
    assert len(sync1_transactions) == 3
    assert isinstance(sync1_transactions[0], TransferInitialTransaction)
    assert sync1_transactions[0].dataset == "/one"
    assert sync1_transactions[0].snapshot == _SNAP_A
    assert isinstance(sync1_transactions[1], TransferIncrementalTransaction)
    assert sync1_transactions[1].dataset == "/one"
    assert sync1_transactions[1].from_snapshot == _SNAP_A
    assert sync1_transactions[1].to_snapshot == _SNAP_B
    assert isinstance(sync1_transactions[2], TransferIncrementalTransaction)
    assert sync1_transactions[2].dataset == "/one"
    assert sync1_transactions[2].from_snapshot == _SNAP_B
    assert sync1_transactions[2].to_snapshot == _SNAP_C

    # step 2: free — removes snap_a, leaving snap_c as the last common snapshot
    res_free = ctx.abgleich(Subcmd.free, *json_args, "-y", src, tgt)
    res_free.assert_exitcode(0)

    free_transactions = ctx.parse_transactions(res_free.stdout, json = json)
    assert len(free_transactions) == 2
    assert isinstance(free_transactions[0], DestroySnapshotTransaction)
    assert free_transactions[0].dataset == "/one"
    assert free_transactions[0].snapshot == _SNAP_A
    assert isinstance(free_transactions[1], DestroySnapshotTransaction)
    assert free_transactions[1].dataset == "/one"
    assert free_transactions[1].snapshot == _SNAP_B

    # step 3: snap — creates snap_d on source child
    res_snap = ctx.abgleich(Subcmd.snap, *json_args, "-y", src)
    res_snap.assert_exitcode(0)

    snap_transactions = ctx.parse_transactions(res_snap.stdout, json = json)
    assert len(snap_transactions) == 1
    assert isinstance(snap_transactions[0], CreateSnapshotTransaction)
    assert snap_transactions[0].dataset == "/one"
    snap_d = snap_transactions[0].snapshot
    assert snap_d != _SNAP_C  # sanity: a genuinely new snapshot was created

    # step 4: incremental sync — transfers snap_d via snap_c as base
    res_sync2 = ctx.abgleich(Subcmd.sync, *json_args, "-y", src, tgt)
    res_sync2.assert_exitcode(0)

    sync2_transactions = ctx.parse_transactions(res_sync2.stdout, json = json)
    assert len(sync2_transactions) == 1
    assert isinstance(sync2_transactions[0], TransferIncrementalTransaction)
    assert sync2_transactions[0].dataset == "/one"
    assert sync2_transactions[0].from_snapshot == _SNAP_C
    assert sync2_transactions[0].to_snapshot == snap_d

    ctx.reload()

    # source child: snap_c, snap_d
    src_snaps = list((ctx[Host.localhost][_ZPOOL_SRC] / "one").snapshots)
    assert len(src_snaps) == 2
    assert src_snaps[0].name == _SNAP_C
    assert src_snaps[1].name == snap_d

    # target child: snap_a, snap_b, snap_c, snap_d
    tgt_snaps = list((ctx[Host.localhost][_ZPOOL_TGT] / "one").snapshots)
    assert len(tgt_snaps) == 4
    assert tgt_snaps[0].name == _SNAP_A
    assert tgt_snaps[1].name == _SNAP_B
    assert tgt_snaps[2].name == _SNAP_C
    assert tgt_snaps[3].name == snap_d
