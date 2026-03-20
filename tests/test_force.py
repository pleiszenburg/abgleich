from datetime import datetime, timedelta

import pytest

from .lib import (
    AProperties,
    Command,
    Context,
    CreateSnapshotTransaction,
    DestroySnapshotTransaction,
    Environment,
    Filesystem,
    Host,
    MntLocal,
    Snap,
    Snapshot,
    SnapshotFormat,
    Subcmd,
    TestConfig,
    TransferIncrementalTransaction,
    TransferInitialTransaction,
    Zpool,
)


_ZPOOL_A   = "foo"
_ZPOOL_SRC = "src"
_ZPOOL_TGT = "tgt"
_DT     = datetime.now()
_SNAP_A = SnapshotFormat.format_(dt = _DT)
_SNAP_B = SnapshotFormat.format_(dt = _DT + timedelta(seconds = 1))
_SNAP_C = SnapshotFormat.format_(dt = _DT + timedelta(seconds = 2))


@pytest.mark.parametrize("json", (False, True))
@pytest.mark.parametrize("force", (
    pytest.param(False, id = "no_force"),
    pytest.param(True,  id = "force"),
))
@Environment(TestConfig(
    zpools = [
        Zpool(
            name = _ZPOOL_A,
            aproperties = AProperties.from_defaults(),
            datasets = [
                Filesystem(name = "one"),
                Filesystem(name = "two"),
            ],
        ),
    ],
))
def test_snap_force(ctx: Context, force: bool, json: bool):
    """
    --force causes snap to attempt all transactions even if the first fails.

    The "one" dataset has ``snapshot_limit=0`` set before the run, so
    ``zfs snapshot foo/one@...`` is rejected immediately.  Without --force
    abgleich stops after that first failure and the child ``/two`` is never
    snapshotted.  With --force the failure is noted but execution continues
    and the ``/two`` snapshot is created successfully, after which abgleich
    exits non-zero because one transaction failed.

    Transaction order: "one" (``/one``) is always first in the ZFS inventory,
    ``/two`` second.  The test verifies ZFS state rather than transaction
    output to confirm which transactions were executed.
    """

    location = f"flashheart%{_ZPOOL_A:s}/"  # this test only makes sense for non-root user
    json_args  = ("-j",) if json  else tuple()
    force_args = ("-f",) if force else tuple()

    # Prevent creating a snapshot on the "one" dataset for regular users.
    Command(
        "zpool", "set", "feature@filesystem_limits=enabled", _ZPOOL_A
    ).with_sudo().on_host(Host.localhost).run().assert_exitcode(0)
    Command(
        "zfs", "set", "snapshot_limit=0", f"{_ZPOOL_A:s}/one"
    ).with_sudo().on_host(Host.localhost).run().assert_exitcode(0)
    Command(
        "zfs", "allow", "flashheart", "snapshot", _ZPOOL_A
    ).with_sudo().on_host(Host.localhost).run().assert_exitcode(0)

    res = ctx.abgleich(Subcmd.snap, *json_args, *force_args, "-y", location)
    res.assert_exitcode(1)

    transactions = ctx.parse_transactions(res.stdout, json = json)
    assert len(transactions) == 2  # both planned regardless of force flag
    assert transactions[0].dataset == "one"
    assert transactions[1].dataset == "two"

    ctx.reload()

    # Root snapshot always fails (snapshot_limit=0 is set regardless of force).
    assert len(list(ctx[Host.localhost][_ZPOOL_A].snapshots)) == 0
    assert len(list((ctx[Host.localhost][_ZPOOL_A] / "one").snapshots)) == 0

    two_snaps = list((ctx[Host.localhost][_ZPOOL_A] / "two").snapshots)
    if force:
        # /two snapshot was attempted and succeeded despite the root failure.
        assert len(two_snaps) == 1
    else:
        # /two snapshot was never attempted after the root failure.
        assert len(two_snaps) == 0


@pytest.mark.parametrize("json", (False, True))
@pytest.mark.parametrize("force", (
    pytest.param(False, id = "no_force"),
    pytest.param(True,  id = "force"),
))
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
    ],
))
def test_free_force(ctx: Context, force: bool, json: bool):
    """
    --force causes free to attempt all destroy transactions even if the first fails.

    Source ``/one`` carries three snapshots [snap_a, snap_b, snap_c] with
    overlap=1.  After syncing to target, ``zfs clone src/one@snap_a`` creates
    a dependent clone, making ``zfs destroy src/one@snap_a`` fail because
    clones cannot be detached by a plain destroy.  The second planned destroy
    (snap_b) is independent of the clone and succeeds.

    Without --force abgleich stops after snap_a's failure, leaving snap_b
    intact on the source.  With --force it notes the failure and proceeds:
    snap_a stays (blocked by the clone) while snap_b is destroyed.
    """

    src = f"root%{_ZPOOL_SRC:s}"
    tgt = f"root%{_ZPOOL_TGT:s}"
    json_args  = ("-j",) if json  else tuple()
    force_args = ("-f",) if force else tuple()

    # Step 1: sync — establishes [snap_a, snap_b, snap_c] as common snapshots.
    res_sync = ctx.abgleich(Subcmd.sync, *json_args, "-y", src, tgt)
    res_sync.assert_exitcode(0)

    # Clone snap_a so that zfs destroy src/one@snap_a fails at execution time.
    # The clone lives in the same pool and is cleaned up when the pool is destroyed.
    src_one  = (ctx[Host.localhost][_ZPOOL_SRC] / "one").full_name
    src_root = ctx[Host.localhost][_ZPOOL_SRC].full_name
    Command(
        "zfs", "clone",
        f"{src_one:s}@{_SNAP_A:s}",
        f"{src_root:s}/one_clone",
    ).with_sudo().on_host(Host.localhost).run().assert_exitcode(0)

    # Step 2: free — with overlap=1 and 3 common snaps, plans destroy snap_a
    # then destroy snap_b (snap_c is the sole kept snapshot).
    res_free = ctx.abgleich(Subcmd.free, *json_args, *force_args, "-y", src, tgt)
    res_free.assert_exitcode(1)

    transactions = ctx.parse_transactions(res_free.stdout, json = json)
    assert len(transactions) == 2
    assert isinstance(transactions[0], DestroySnapshotTransaction)
    assert transactions[0].dataset == "/one"
    assert transactions[0].snapshot == _SNAP_A
    assert isinstance(transactions[1], DestroySnapshotTransaction)
    assert transactions[1].dataset == "/one"
    assert transactions[1].snapshot == _SNAP_B

    ctx.reload()

    src_snaps = {s.name for s in (ctx[Host.localhost][_ZPOOL_SRC] / "one").snapshots}

    # snap_a cannot be destroyed while the clone exists — always remains.
    assert _SNAP_A in src_snaps
    # snap_c is the kept overlap — always remains.
    assert _SNAP_C in src_snaps

    if force:
        # snap_b was attempted and destroyed despite snap_a's failure.
        assert _SNAP_B not in src_snaps
        assert len(src_snaps) == 2  # snap_a, snap_c
    else:
        # snap_b was not attempted after snap_a failed.
        assert _SNAP_B in src_snaps
        assert len(src_snaps) == 3  # snap_a, snap_b, snap_c

    # cleanup
    Command(
        "zfs", "destroy", f"{src_root:s}/one_clone",
    ).with_sudo().on_host(Host.localhost).run().assert_exitcode(0)
    ctx.reload()


@pytest.mark.parametrize("json", (False, True))
@pytest.mark.parametrize("force", (
    pytest.param(False, id = "no_force"),
    pytest.param(True,  id = "force"),
))
@Environment(TestConfig(
    zpools = [
        Zpool(
            name = _ZPOOL_SRC,
            aproperties = AProperties.from_defaults(snap = Snap.never),
            datasets = [
                Filesystem(
                    name = "one",
                    aproperties = AProperties.from_defaults(snap = Snap.always),
                    snapshots = [Snapshot(_SNAP_A)],
                ),
                Filesystem(
                    name = "two",
                    aproperties = AProperties.from_defaults(snap = Snap.always),
                    snapshots = [Snapshot(_SNAP_A)],
                ),
            ],
        ),
        Zpool(name = _ZPOOL_TGT, mountpoint = MntLocal(None)),
    ],
))
def test_sync_force(ctx: Context, force: bool, json: bool):
    """
    --force causes sync to attempt all transfer transactions even if the first fails.

    Source carries two child datasets, each starting with snap_a.  After an
    initial sync both are mirrored to target.  A second snap creates snap_b on
    both source children.  Then ``snapshot_limit=1`` is set on *target* ``/one``
    (which already holds exactly one snapshot), so the incremental receive that
    would add snap_b to it is rejected by ZFS.  The incremental receive for
    ``/two`` is unaffected (no limit set there).

    Transaction order: ``/one`` sorts before ``/two``, so the failing
    transaction is always first.  Without --force abgleich stops after ``/one``
    fails and ``/two`` never receives snap_b.  With --force both are attempted:
    ``/one`` fails (snap_b absent from target) and ``/two`` succeeds.
    """

    src = f"root%{_ZPOOL_SRC:s}"
    tgt = f"root%{_ZPOOL_TGT:s}"
    json_args  = ("-j",) if json  else tuple()
    force_args = ("-f",) if force else tuple()

    # Step 1: initial sync — transfers snap_a to target for both /one and /two.
    res_sync1 = ctx.abgleich(Subcmd.sync, *json_args, "-y", src, tgt)
    res_sync1.assert_exitcode(0)

    sync1_transactions = ctx.parse_transactions(res_sync1.stdout, json = json)
    assert len(sync1_transactions) == 2
    assert isinstance(sync1_transactions[0], TransferInitialTransaction)
    assert sync1_transactions[0].dataset == "/one"
    assert sync1_transactions[0].snapshot == _SNAP_A
    assert isinstance(sync1_transactions[1], TransferInitialTransaction)
    assert sync1_transactions[1].dataset == "/two"
    assert sync1_transactions[1].snapshot == _SNAP_A

    # Step 2: snap — creates snap_b on both source children (snap=always).
    res_snap = ctx.abgleich(Subcmd.snap, *json_args, "-y", src)
    res_snap.assert_exitcode(0)

    snap_transactions = ctx.parse_transactions(res_snap.stdout, json = json)
    assert len(snap_transactions) == 2
    assert isinstance(snap_transactions[0], CreateSnapshotTransaction)
    assert snap_transactions[0].dataset == "/one"
    snap_b = snap_transactions[0].snapshot
    assert snap_b != _SNAP_A  # sanity: a genuinely new snapshot was created

    # Step 3: cap target /one at its current count of one snapshot so that
    # receiving snap_b there is rejected by ZFS ("dataset limit exceeded").
    tgt = f"flashheart%{_ZPOOL_TGT:s}"  # from here on, this test only makes sense for non-root user
    Command(
        "zpool", "set", "feature@filesystem_limits=enabled", _ZPOOL_TGT
    ).with_sudo().on_host(Host.localhost).run().assert_exitcode(0)
    Command(
        "zfs", "set", "snapshot_limit=1", f"{_ZPOOL_TGT:s}/one"
    ).with_sudo().on_host(Host.localhost).run().assert_exitcode(0)
    Command(
        "zfs", "allow", "flashheart", "receive,create,mount,mountpoint,compression,recordsize,quota,refquota,reservation,refreservation", _ZPOOL_TGT
    ).with_sudo().on_host(Host.localhost).run().assert_exitcode(0)

    # Step 4: sync — plans incremental snap_a→snap_b for /one and /two.
    res_sync2 = ctx.abgleich(Subcmd.sync, *json_args, *force_args, "-y", src, tgt)
    res_sync2.assert_exitcode(1)

    sync2_transactions = ctx.parse_transactions(res_sync2.stdout, json = json)
    assert len(sync2_transactions) == 2  # both planned regardless of force flag
    assert isinstance(sync2_transactions[0], TransferIncrementalTransaction)
    assert sync2_transactions[0].dataset == "/one"
    assert isinstance(sync2_transactions[1], TransferIncrementalTransaction)
    assert sync2_transactions[1].dataset == "/two"

    ctx.reload()

    # /one: snapshot_limit=1 blocked the incremental receive — still only snap_a.
    one_tgt = list((ctx[Host.localhost][_ZPOOL_TGT] / "one").snapshots)
    assert len(one_tgt) == 1
    assert one_tgt[0].name == _SNAP_A

    if force:
        # /two was attempted and succeeded despite /one's failure.
        two_tgt = list((ctx[Host.localhost][_ZPOOL_TGT] / "two").snapshots)
        assert len(two_tgt) == 2
        assert two_tgt[0].name == _SNAP_A
        assert two_tgt[1].name == snap_b
    else:
        # /two was not attempted after /one failed.
        two_tgt = list((ctx[Host.localhost][_ZPOOL_TGT] / "two").snapshots)
        assert len(two_tgt) == 1
        assert two_tgt[0].name == _SNAP_A
