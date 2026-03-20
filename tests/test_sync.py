from datetime import datetime
from typing import Optional

import pytest

from .lib import (
    AProperties,
    Context,
    CreateSnapshotTransaction,
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
_SNAP = SnapshotFormat.format_(dt = datetime.now())


@pytest.mark.parametrize("json", (False, True))
@pytest.mark.parametrize("route", (None, "", "localhost", "remotehost", "remotehost/remotehost"))
@Environment(TestConfig(
    zpools = [
        Zpool(name = _ZPOOL_SRC, aproperties = AProperties.from_defaults(), datasets = [
            Filesystem(name = "one", snapshots = [
                Snapshot(_SNAP),
            ]),
        ]),
        Zpool(name = _ZPOOL_TGT),
    ]
))
def test_sync_min_initial(ctx: Context, route: Optional[str], json: bool):
    """
    minimal sync test: initial transfer of a single child filesystem

    Source has one child dataset with one snapshot; target is an empty zpool.
    The root datasets of both zpools carry no snapshots, so only the child
    dataset triggers a transaction.  Sync must produce exactly one
    TransferInitial transaction and, after execution, leave that snapshot
    on the target while leaving the source unchanged.
    """

    src = f"root%{_ZPOOL_SRC:s}"
    tgt = f"root%{_ZPOOL_TGT:s}"
    if route is not None:
        src = f"{route:s}:{src:s}"
        tgt = f"{route:s}:{tgt:s}"
    json_args = ("-j",) if json else tuple()

    res = ctx.abgleich(Subcmd.sync, *json_args, "-y", src, tgt)
    res.assert_exitcode(0)

    transactions = ctx.parse_transactions(res.stdout, json = json)

    assert len(transactions) == 1
    assert isinstance(transactions[0], TransferInitialTransaction)
    assert transactions[0].dataset == "/one"
    assert transactions[0].snapshot == _SNAP

    ctx.reload()

    # target must now carry the transferred snapshot
    one_snaps = set((ctx[Host.localhost][_ZPOOL_TGT] / "one").snapshots)
    assert len(one_snaps) == 1
    assert one_snaps.pop().name == _SNAP

    # source must be unchanged
    src_snaps = set((ctx[Host.localhost][_ZPOOL_SRC] / "one").snapshots)
    assert len(src_snaps) == 1
    assert src_snaps.pop().name == _SNAP

    # target root must have no snapshots (only the child was synced)
    assert len(set(ctx[Host.localhost][_ZPOOL_TGT].snapshots)) == 0


@pytest.mark.parametrize("json", (False, True))
@pytest.mark.parametrize("route", (None, "", "localhost", "remotehost", "remotehost/remotehost"))
@Environment(TestConfig(
    zpools = [
        Zpool(name = _ZPOOL_SRC, aproperties = AProperties.from_defaults(snap = Snap.never), datasets = [
            Filesystem(name = "one", aproperties = AProperties.from_defaults(snap = Snap.always), snapshots = [
                Snapshot(_SNAP),
            ]),
        ]),
        Zpool(name = _ZPOOL_TGT),
    ]
))
def test_sync_min_incremental(ctx: Context, route: Optional[str], json: bool):
    """
    incremental sync test: transfer of a snapshot added after initial sync

    Step 1 – initial sync: transfers _SNAP from source to target (TransferInitial).
    Step 2 – snap: creates a fresh snapshot (snap_b) on the source child dataset.
    Step 3 – incremental sync: transfers snap_b to the target (TransferIncremental).

    After step 3 the target must carry both _SNAP and snap_b in creation order;
    the source is unchanged.

    Design notes
    ------------
    The source root is configured with snap=never so that step 2 only creates a
    snapshot for the child dataset, keeping the transaction count predictable.

    snap_b is intentionally created via 'abgleich snap' (step 2) rather than via
    the test infrastructure directly.  This guarantees that bar/one@_SNAP received
    in step 1 shares its ZFS creation timestamp with foo/one@_SNAP (zfs receive
    preserves the source creation time), which is required by the common-snapshot
    equality check inside the sync engine.
    """

    src = f"root%{_ZPOOL_SRC:s}"
    tgt = f"root%{_ZPOOL_TGT:s}"
    if route is not None:
        src = f"{route:s}:{src:s}"
        tgt = f"{route:s}:{tgt:s}"
    json_args = ("-j",) if json else tuple()

    # step 1: initial sync — transfers _SNAP from source child to target
    res_sync1 = ctx.abgleich(Subcmd.sync, *json_args, "-y", src, tgt)
    res_sync1.assert_exitcode(0)

    transactions = ctx.parse_transactions(res_sync1.stdout, json = json)
    assert len(transactions) == 1
    assert isinstance(transactions[0], TransferInitialTransaction)
    assert transactions[0].dataset == "/one"
    assert transactions[0].snapshot == _SNAP

    # step 2: create a second snapshot on the source child via abgleich snap
    res_snap = ctx.abgleich(Subcmd.snap, *json_args, "-y", src)
    res_snap.assert_exitcode(0)

    snap_transactions = ctx.parse_transactions(res_snap.stdout, json = json)
    assert len(snap_transactions) == 1
    assert isinstance(snap_transactions[0], CreateSnapshotTransaction)
    assert snap_transactions[0].dataset == "/one"
    snap_b = snap_transactions[0].snapshot
    assert snap_b != _SNAP  # sanity: a genuinely new snapshot was created

    # step 3: incremental sync — transfers snap_b to the target
    res_sync2 = ctx.abgleich(Subcmd.sync, *json_args, "-y", src, tgt)
    res_sync2.assert_exitcode(0)

    transactions = ctx.parse_transactions(res_sync2.stdout, json = json)
    assert len(transactions) == 1
    assert isinstance(transactions[0], TransferIncrementalTransaction)
    assert transactions[0].dataset == "/one"
    assert transactions[0].from_snapshot == _SNAP
    assert transactions[0].to_snapshot == snap_b

    ctx.reload()

    # target must carry both snapshots in creation order
    tgt_snaps = list((ctx[Host.localhost][_ZPOOL_TGT] / "one").snapshots)
    assert len(tgt_snaps) == 2
    assert tgt_snaps[0].name == _SNAP
    assert tgt_snaps[1].name == snap_b

    # source must also carry both snapshots, unchanged by sync
    src_snaps = list((ctx[Host.localhost][_ZPOOL_SRC] / "one").snapshots)
    assert len(src_snaps) == 2
    assert src_snaps[0].name == _SNAP
    assert src_snaps[1].name == snap_b


@pytest.mark.parametrize("json", (False, True))
@Environment(TestConfig(
    nodes = dict(
        current_a = dict(
            required = True,
            zpools = [
                Zpool(name = _ZPOOL_SRC, aproperties = AProperties.from_defaults(), datasets = [
                    Filesystem(name = "one", snapshots = [
                        Snapshot(_SNAP),
                    ]),
                ]),
            ],
        ),
        current_b = dict(
            required = True,
            zpools = [
                Zpool(name = _ZPOOL_TGT),
            ],
        ),
    ),
))
def test_sync_push_initial(ctx: Context, json: bool):
    """
    minimal sync test: initial transfer of a single child filesystem, push to remote

    Source has one child dataset with one snapshot; target is an empty zpool.
    The root datasets of both zpools carry no snapshots, so only the child
    dataset triggers a transaction.  Sync must produce exactly one
    TransferInitial transaction and, after execution, leave that snapshot
    on the target while leaving the source unchanged.
    """

    src = f"{Host.localhost.to_host_name():s}:root%{_ZPOOL_SRC:s}"
    tgt = f"{Host.current_b.to_host_name():s}:root%{_ZPOOL_TGT:s}"
    json_args = ("-j",) if json else tuple()

    res = ctx.abgleich(Subcmd.sync, *json_args, "-y", src, tgt)
    res.assert_exitcode(0)

    transactions = ctx.parse_transactions(res.stdout, json = json)

    assert len(transactions) == 1
    assert isinstance(transactions[0], TransferInitialTransaction)
    assert transactions[0].dataset == "/one"
    assert transactions[0].snapshot == _SNAP

    ctx.reload()

    # target must now carry the transferred snapshot
    one_snaps = set((ctx[Host.current_b][_ZPOOL_TGT] / "one").snapshots)
    assert len(one_snaps) == 1
    assert one_snaps.pop().name == _SNAP

    # source must be unchanged
    src_snaps = set((ctx[Host.localhost][_ZPOOL_SRC] / "one").snapshots)
    assert len(src_snaps) == 1
    assert src_snaps.pop().name == _SNAP

    # target root must have no snapshots (only the child was synced)
    assert len(set(ctx[Host.current_b][_ZPOOL_TGT].snapshots)) == 0


@pytest.mark.parametrize("json", (False, True))
@Environment(TestConfig(
    nodes = dict(
        current_a = dict(
            required = True,
            zpools = [
                Zpool(name = _ZPOOL_SRC, aproperties = AProperties.from_defaults(snap = Snap.never), datasets = [
                    Filesystem(name = "one", aproperties = AProperties.from_defaults(snap = Snap.always), snapshots = [
                        Snapshot(_SNAP),
                    ]),
                ]),
            ],
        ),
        current_b = dict(
            required = True,
            zpools = [
                Zpool(name = _ZPOOL_TGT),
            ],
        ),
    ),
))
def test_sync_push_incremental(ctx: Context, json: bool):
    """
    incremental sync test: transfer of a snapshot added after initial sync, push to remote

    Step 1 – initial sync: transfers _SNAP from source to target (TransferInitial).
    Step 2 – snap: creates a fresh snapshot (snap_b) on the source child dataset.
    Step 3 – incremental sync: transfers snap_b to the target (TransferIncremental).

    After step 3 the target must carry both _SNAP and snap_b in creation order;
    the source is unchanged.

    Design notes
    ------------
    The source root is configured with snap=never so that step 2 only creates a
    snapshot for the child dataset, keeping the transaction count predictable.

    snap_b is intentionally created via 'abgleich snap' (step 2) rather than via
    the test infrastructure directly.  This guarantees that bar/one@_SNAP received
    in step 1 shares its ZFS creation timestamp with foo/one@_SNAP (zfs receive
    preserves the source creation time), which is required by the common-snapshot
    equality check inside the sync engine.
    """

    src = f"{Host.localhost.to_host_name():s}:root%{_ZPOOL_SRC:s}"
    tgt = f"{Host.current_b.to_host_name():s}:root%{_ZPOOL_TGT:s}"
    json_args = ("-j",) if json else tuple()

    # step 1: initial sync — transfers _SNAP from source child to target
    res_sync1 = ctx.abgleich(Subcmd.sync, *json_args, "-y", src, tgt)
    res_sync1.assert_exitcode(0)

    transactions = ctx.parse_transactions(res_sync1.stdout, json = json)
    assert len(transactions) == 1
    assert isinstance(transactions[0], TransferInitialTransaction)
    assert transactions[0].dataset == "/one"
    assert transactions[0].snapshot == _SNAP

    # step 2: create a second snapshot on the source child via abgleich snap
    res_snap = ctx.abgleich(Subcmd.snap, *json_args, "-y", src)
    res_snap.assert_exitcode(0)

    snap_transactions = ctx.parse_transactions(res_snap.stdout, json = json)
    assert len(snap_transactions) == 1
    assert isinstance(snap_transactions[0], CreateSnapshotTransaction)
    assert snap_transactions[0].dataset == "/one"
    snap_b = snap_transactions[0].snapshot
    assert snap_b != _SNAP  # sanity: a genuinely new snapshot was created

    # step 3: incremental sync — transfers snap_b to the target
    res_sync2 = ctx.abgleich(Subcmd.sync, *json_args, "-y", src, tgt)
    res_sync2.assert_exitcode(0)

    transactions = ctx.parse_transactions(res_sync2.stdout, json = json)
    assert len(transactions) == 1
    assert isinstance(transactions[0], TransferIncrementalTransaction)
    assert transactions[0].dataset == "/one"
    assert transactions[0].from_snapshot == _SNAP
    assert transactions[0].to_snapshot == snap_b

    ctx.reload()

    # target must carry both snapshots in creation order
    tgt_snaps = list((ctx[Host.current_b][_ZPOOL_TGT] / "one").snapshots)
    assert len(tgt_snaps) == 2
    assert tgt_snaps[0].name == _SNAP
    assert tgt_snaps[1].name == snap_b

    # source must also carry both snapshots, unchanged by sync
    src_snaps = list((ctx[Host.localhost][_ZPOOL_SRC] / "one").snapshots)
    assert len(src_snaps) == 2
    assert src_snaps[0].name == _SNAP
    assert src_snaps[1].name == snap_b


@pytest.mark.parametrize("json", (False, True))
@Environment(TestConfig(
    nodes = dict(
        current_b = dict(
            required = True,
            zpools = [
                Zpool(name = _ZPOOL_SRC, aproperties = AProperties.from_defaults(), datasets = [
                    Filesystem(name = "one", snapshots = [
                        Snapshot(_SNAP),
                    ]),
                ]),
            ],
        ),
        current_a = dict(
            required = True,
            zpools = [
                Zpool(name = _ZPOOL_TGT),
            ],
        ),
    ),
))
def test_sync_pull_initial(ctx: Context, json: bool):
    """
    minimal sync test: initial transfer of a single child filesystem, pull from remote

    Source has one child dataset with one snapshot; target is an empty zpool.
    The root datasets of both zpools carry no snapshots, so only the child
    dataset triggers a transaction.  Sync must produce exactly one
    TransferInitial transaction and, after execution, leave that snapshot
    on the target while leaving the source unchanged.
    """

    src = f"{Host.current_b.to_host_name():s}:root%{_ZPOOL_SRC:s}"
    tgt = f"{Host.localhost.to_host_name():s}:root%{_ZPOOL_TGT:s}"
    json_args = ("-j",) if json else tuple()

    res = ctx.abgleich(Subcmd.sync, *json_args, "-y", src, tgt)
    res.assert_exitcode(0)

    transactions = ctx.parse_transactions(res.stdout, json = json)

    assert len(transactions) == 1
    assert isinstance(transactions[0], TransferInitialTransaction)
    assert transactions[0].dataset == "/one"
    assert transactions[0].snapshot == _SNAP

    ctx.reload()

    # target must now carry the transferred snapshot
    one_snaps = set((ctx[Host.localhost][_ZPOOL_TGT] / "one").snapshots)
    assert len(one_snaps) == 1
    assert one_snaps.pop().name == _SNAP

    # source must be unchanged
    src_snaps = set((ctx[Host.current_b][_ZPOOL_SRC] / "one").snapshots)
    assert len(src_snaps) == 1
    assert src_snaps.pop().name == _SNAP

    # target root must have no snapshots (only the child was synced)
    assert len(set(ctx[Host.localhost][_ZPOOL_TGT].snapshots)) == 0


@pytest.mark.parametrize("json", (False, True))
@Environment(TestConfig(
    nodes = dict(
        current_b = dict(
            required = True,
            zpools = [
                Zpool(name = _ZPOOL_SRC, aproperties = AProperties.from_defaults(snap = Snap.never), datasets = [
                    Filesystem(name = "one", aproperties = AProperties.from_defaults(snap = Snap.always), snapshots = [
                        Snapshot(_SNAP),
                    ]),
                ]),
            ],
        ),
        current_a = dict(
            required = True,
            zpools = [
                Zpool(name = _ZPOOL_TGT),
            ],
        ),
    ),
))
def test_sync_pull_incremental(ctx: Context, json: bool):
    """
    incremental sync test: transfer of a snapshot added after initial sync, pull from remote

    Step 1 – initial sync: transfers _SNAP from source to target (TransferInitial).
    Step 2 – snap: creates a fresh snapshot (snap_b) on the source child dataset.
    Step 3 – incremental sync: transfers snap_b to the target (TransferIncremental).

    After step 3 the target must carry both _SNAP and snap_b in creation order;
    the source is unchanged.

    Design notes
    ------------
    The source root is configured with snap=never so that step 2 only creates a
    snapshot for the child dataset, keeping the transaction count predictable.

    snap_b is intentionally created via 'abgleich snap' (step 2) rather than via
    the test infrastructure directly.  This guarantees that bar/one@_SNAP received
    in step 1 shares its ZFS creation timestamp with foo/one@_SNAP (zfs receive
    preserves the source creation time), which is required by the common-snapshot
    equality check inside the sync engine.
    """

    src = f"{Host.current_b.to_host_name():s}:root%{_ZPOOL_SRC:s}"
    tgt = f"{Host.localhost.to_host_name():s}:root%{_ZPOOL_TGT:s}"
    json_args = ("-j",) if json else tuple()

    # step 1: initial sync — transfers _SNAP from source child to target
    res_sync1 = ctx.abgleich(Subcmd.sync, *json_args, "-y", src, tgt)
    res_sync1.assert_exitcode(0)

    transactions = ctx.parse_transactions(res_sync1.stdout, json = json)
    assert len(transactions) == 1
    assert isinstance(transactions[0], TransferInitialTransaction)
    assert transactions[0].dataset == "/one"
    assert transactions[0].snapshot == _SNAP

    # step 2: create a second snapshot on the source child via abgleich snap
    res_snap = ctx.abgleich(Subcmd.snap, *json_args, "-y", src)
    res_snap.assert_exitcode(0)

    snap_transactions = ctx.parse_transactions(res_snap.stdout, json = json)
    assert len(snap_transactions) == 1
    assert isinstance(snap_transactions[0], CreateSnapshotTransaction)
    assert snap_transactions[0].dataset == "/one"
    snap_b = snap_transactions[0].snapshot
    assert snap_b != _SNAP  # sanity: a genuinely new snapshot was created

    # step 3: incremental sync — transfers snap_b to the target
    res_sync2 = ctx.abgleich(Subcmd.sync, *json_args, "-y", src, tgt)
    res_sync2.assert_exitcode(0)

    transactions = ctx.parse_transactions(res_sync2.stdout, json = json)
    assert len(transactions) == 1
    assert isinstance(transactions[0], TransferIncrementalTransaction)
    assert transactions[0].dataset == "/one"
    assert transactions[0].from_snapshot == _SNAP
    assert transactions[0].to_snapshot == snap_b

    ctx.reload()

    # target must carry both snapshots in creation order
    tgt_snaps = list((ctx[Host.localhost][_ZPOOL_TGT] / "one").snapshots)
    assert len(tgt_snaps) == 2
    assert tgt_snaps[0].name == _SNAP
    assert tgt_snaps[1].name == snap_b

    # source must also carry both snapshots, unchanged by sync
    src_snaps = list((ctx[Host.current_b][_ZPOOL_SRC] / "one").snapshots)
    assert len(src_snaps) == 2
    assert src_snaps[0].name == _SNAP
    assert src_snaps[1].name == snap_b


@pytest.mark.parametrize("json", (False, True))
@Environment(TestConfig(
    nodes = dict(
        other_a = dict(
            required = True,
            zpools = [
                Zpool(name = _ZPOOL_SRC, aproperties = AProperties.from_defaults(), datasets = [
                    Filesystem(name = "one", snapshots = [
                        Snapshot(_SNAP),
                    ]),
                ]),
            ],
        ),
        other_b = dict(
            required = True,
            zpools = [
                Zpool(name = _ZPOOL_TGT),
            ],
        ),
    ),
))
def test_sync_pp_initial(ctx: Context, json: bool):
    """
    minimal sync test: initial transfer of a single child filesystem, pull from remote, push to other remote

    Source has one child dataset with one snapshot; target is an empty zpool.
    The root datasets of both zpools carry no snapshots, so only the child
    dataset triggers a transaction.  Sync must produce exactly one
    TransferInitial transaction and, after execution, leave that snapshot
    on the target while leaving the source unchanged.
    """

    src = f"{Host.other_a.to_host_name():s}:root%{_ZPOOL_SRC:s}"
    tgt = f"{Host.other_b.to_host_name():s}:root%{_ZPOOL_TGT:s}"
    json_args = ("-j",) if json else tuple()

    res = ctx.abgleich(Subcmd.sync, *json_args, "-y", src, tgt)
    res.assert_exitcode(0)

    transactions = ctx.parse_transactions(res.stdout, json = json)

    assert len(transactions) == 1
    assert isinstance(transactions[0], TransferInitialTransaction)
    assert transactions[0].dataset == "/one"
    assert transactions[0].snapshot == _SNAP

    ctx.reload()

    # target must now carry the transferred snapshot
    one_snaps = set((ctx[Host.other_b][_ZPOOL_TGT] / "one").snapshots)
    assert len(one_snaps) == 1
    assert one_snaps.pop().name == _SNAP

    # source must be unchanged
    src_snaps = set((ctx[Host.other_a][_ZPOOL_SRC] / "one").snapshots)
    assert len(src_snaps) == 1
    assert src_snaps.pop().name == _SNAP

    # target root must have no snapshots (only the child was synced)
    assert len(set(ctx[Host.other_b][_ZPOOL_TGT].snapshots)) == 0


@pytest.mark.parametrize("json", (False, True))
@Environment(TestConfig(
    nodes = dict(
        other_a = dict(
            required = True,
            zpools = [
                Zpool(name = _ZPOOL_SRC, aproperties = AProperties.from_defaults(snap = Snap.never), datasets = [
                    Filesystem(name = "one", aproperties = AProperties.from_defaults(snap = Snap.always), snapshots = [
                        Snapshot(_SNAP),
                    ]),
                ]),
            ],
        ),
        other_b = dict(
            required = True,
            zpools = [
                Zpool(name = _ZPOOL_TGT),
            ],
        ),
    ),
))
def test_sync_pp_incremental(ctx: Context, json: bool):
    """
    incremental sync test: transfer of a snapshot added after initial sync, pull from remote, push to other remote

    Step 1 – initial sync: transfers _SNAP from source to target (TransferInitial).
    Step 2 – snap: creates a fresh snapshot (snap_b) on the source child dataset.
    Step 3 – incremental sync: transfers snap_b to the target (TransferIncremental).

    After step 3 the target must carry both _SNAP and snap_b in creation order;
    the source is unchanged.

    Design notes
    ------------
    The source root is configured with snap=never so that step 2 only creates a
    snapshot for the child dataset, keeping the transaction count predictable.

    snap_b is intentionally created via 'abgleich snap' (step 2) rather than via
    the test infrastructure directly.  This guarantees that bar/one@_SNAP received
    in step 1 shares its ZFS creation timestamp with foo/one@_SNAP (zfs receive
    preserves the source creation time), which is required by the common-snapshot
    equality check inside the sync engine.
    """

    src = f"{Host.other_a.to_host_name():s}:root%{_ZPOOL_SRC:s}"
    tgt = f"{Host.other_b.to_host_name():s}:root%{_ZPOOL_TGT:s}"
    json_args = ("-j",) if json else tuple()

    # step 1: initial sync — transfers _SNAP from source child to target
    res_sync1 = ctx.abgleich(Subcmd.sync, *json_args, "-y", src, tgt)
    res_sync1.assert_exitcode(0)

    transactions = ctx.parse_transactions(res_sync1.stdout, json = json)
    assert len(transactions) == 1
    assert isinstance(transactions[0], TransferInitialTransaction)
    assert transactions[0].dataset == "/one"
    assert transactions[0].snapshot == _SNAP

    # step 2: create a second snapshot on the source child via abgleich snap
    res_snap = ctx.abgleich(Subcmd.snap, *json_args, "-y", src)
    res_snap.assert_exitcode(0)

    snap_transactions = ctx.parse_transactions(res_snap.stdout, json = json)
    assert len(snap_transactions) == 1
    assert isinstance(snap_transactions[0], CreateSnapshotTransaction)
    assert snap_transactions[0].dataset == "/one"
    snap_b = snap_transactions[0].snapshot
    assert snap_b != _SNAP  # sanity: a genuinely new snapshot was created

    # step 3: incremental sync — transfers snap_b to the target
    res_sync2 = ctx.abgleich(Subcmd.sync, *json_args, "-y", src, tgt)
    res_sync2.assert_exitcode(0)

    transactions = ctx.parse_transactions(res_sync2.stdout, json = json)
    assert len(transactions) == 1
    assert isinstance(transactions[0], TransferIncrementalTransaction)
    assert transactions[0].dataset == "/one"
    assert transactions[0].from_snapshot == _SNAP
    assert transactions[0].to_snapshot == snap_b

    ctx.reload()

    # target must carry both snapshots in creation order
    tgt_snaps = list((ctx[Host.other_b][_ZPOOL_TGT] / "one").snapshots)
    assert len(tgt_snaps) == 2
    assert tgt_snaps[0].name == _SNAP
    assert tgt_snaps[1].name == snap_b

    # source must also carry both snapshots, unchanged by sync
    src_snaps = list((ctx[Host.other_a][_ZPOOL_SRC] / "one").snapshots)
    assert len(src_snaps) == 2
    assert src_snaps[0].name == _SNAP
    assert src_snaps[1].name == snap_b


@pytest.mark.parametrize("json", (False, True))
@Environment(*(TestConfig(
    zpools = [
        Zpool(
            name = _ZPOOL_SRC,
            datasets = [
                Filesystem(
                    name = "one",
                    aproperties = AProperties.from_defaults(sync = sync),
                    snapshots = [
                        Snapshot("a"),
                        Snapshot("b"),
                        Snapshot("c"),
                    ]
                ),
            ]
        ),
        Zpool(
            name = _ZPOOL_TGT,
            datasets = [
                Filesystem(
                    name = "one",
                    snapshots = [
                        Snapshot("d"),
                        Snapshot("e"),
                        Snapshot("f"),
                    ]
                ),
            ]
        ),
    ]
) for sync in (True, False)))
def test_sync_ignore(ctx: Context, json: bool):
    """
    ignore divergent snapshot sequences, do not sync

    Datasets with identical names but completely different sequences of snapshots.
    Ideally, nothing should happen.
    """

    feature = not (ctx[Host.localhost][_ZPOOL_SRC] / "one").aproperties.sync

    src = f"root%{_ZPOOL_SRC:s}"
    tgt = f"root%{_ZPOOL_TGT:s}"
    json_args = ("-j",) if json else tuple()

    res = ctx.abgleich(Subcmd.sync, *json_args, "-y", src, tgt)

    if not feature:
        res.assert_exitcode(1)
        return

    res.assert_exitcode(0)

    transactions = ctx.parse_transactions(res.stdout, json = json)
    assert len(transactions) == 0
