from datetime import datetime

import pytest

from .lib import (
    AProperties,
    Context,
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


_ZPOOL_SRC = "src"
_ZPOOL_TGT = "tgt"
_SNAP = SnapshotFormat.format_(dt = datetime.now())


@pytest.mark.parametrize("json", (False, True))
@Environment(TestConfig(
    zpools = [
        Zpool(
            name = _ZPOOL_SRC,
            aproperties = AProperties.from_defaults(),
            datasets = [
                Filesystem(name = "one", snapshots = [Snapshot(_SNAP)]),
            ],
        ),
        Zpool(name = _ZPOOL_TGT),
    ],
))
def test_sync_ratelimit_initial(ctx: Context, json: bool):
    """
    ``abgleich sync -r 10m`` inserts ``pv -q -L 10485760`` into the send
    pipeline on the sending host.

    The rate limit is high enough that a small test snapshot completes in
    well under a second.  The test verifies only that the flag is accepted,
    the transfer succeeds, and the snapshot arrives on the target.

    Requires ``pv`` to be installed on the source host.
    """

    src = f"root%{_ZPOOL_SRC:s}"
    tgt = f"root%{_ZPOOL_TGT:s}"
    json_args = ("-j",) if json else tuple()

    res = ctx.abgleich(Subcmd.sync, *json_args, "-r", "10m", "-y", src, tgt)
    res.assert_exitcode(0)

    transactions = ctx.parse_transactions(res.stdout, json = json)
    assert len(transactions) == 1
    assert isinstance(transactions[0], TransferInitialTransaction)
    assert transactions[0].dataset == "/one"
    assert transactions[0].snapshot == _SNAP

    ctx.reload()

    tgt_snaps = list((ctx[Host.localhost][_ZPOOL_TGT] / "one").snapshots)
    assert len(tgt_snaps) == 1
    assert tgt_snaps[0].name == _SNAP


@pytest.mark.parametrize("json", (False, True))
@Environment(TestConfig(
    zpools = [
        Zpool(
            name = _ZPOOL_SRC,
            aproperties = AProperties.from_defaults(snap = Snap.never),
            datasets = [
                Filesystem(
                    name = "one",
                    aproperties = AProperties.from_defaults(snap = Snap.always, overlap = 1),
                    snapshots = [Snapshot(_SNAP)],
                ),
            ],
        ),
        Zpool(name = _ZPOOL_TGT),
    ],
))
def test_sync_ratelimit_incremental(ctx: Context, json: bool):
    """
    Rate limiting also applies to incremental transfers.

    After an initial sync a second snapshot is created on the source.  An
    incremental rate-limited sync must transfer the new snapshot and leave
    both snapshots on the target.
    """

    src = f"root%{_ZPOOL_SRC:s}"
    tgt = f"root%{_ZPOOL_TGT:s}"
    json_args = ("-j",) if json else tuple()

    # Initial sync without rate limit.
    res_sync1 = ctx.abgleich(Subcmd.sync, *json_args, "-y", src, tgt)
    res_sync1.assert_exitcode(0)

    # Create a second snapshot.
    res_snap = ctx.abgleich(Subcmd.snap, *json_args, "-y", src)
    res_snap.assert_exitcode(0)

    # Incremental rate-limited sync.
    res_sync2 = ctx.abgleich(Subcmd.sync, *json_args, "-r", "10m", "-y", src, tgt)
    res_sync2.assert_exitcode(0)

    transactions2 = ctx.parse_transactions(res_sync2.stdout, json = json)
    assert len(transactions2) == 1
    assert isinstance(transactions2[0], TransferIncrementalTransaction)
    assert transactions2[0].dataset == "/one"

    ctx.reload()

    tgt_snaps = list((ctx[Host.localhost][_ZPOOL_TGT] / "one").snapshots)
    assert len(tgt_snaps) == 2


@pytest.mark.parametrize("json", (False, True))
@Environment(TestConfig(
    zpools = [
        Zpool(
            name = _ZPOOL_SRC,
            aproperties = AProperties.from_defaults(),
            datasets = [
                Filesystem(name = "one", snapshots = [Snapshot(_SNAP)]),
            ],
        ),
        Zpool(name = _ZPOOL_TGT),
    ],
))
def test_sync_ratelimit_and_compress(ctx: Context, json: bool):
    """
    ``-r`` and ``-x`` can be combined: the pipeline becomes
    ``zfs send | pv -q -L N | xz -5`` on the source and ``xz -d | zfs receive``
    on the target.  ``zfs send -c`` is suppressed when ``-x`` is active.

    Both ``pv`` and ``xz`` must be installed on the source host; ``xz`` must
    be installed on the target host.
    """

    src = f"root%{_ZPOOL_SRC:s}"
    tgt = f"root%{_ZPOOL_TGT:s}"
    json_args = ("-j",) if json else tuple()

    res = ctx.abgleich(Subcmd.sync, *json_args, "-r", "10m", "-x", "-y", src, tgt)
    res.assert_exitcode(0)

    transactions = ctx.parse_transactions(res.stdout, json = json)
    assert len(transactions) == 1
    assert isinstance(transactions[0], TransferInitialTransaction)
    assert transactions[0].dataset == "/one"
    assert transactions[0].snapshot == _SNAP

    ctx.reload()

    tgt_snaps = list((ctx[Host.localhost][_ZPOOL_TGT] / "one").snapshots)
    assert len(tgt_snaps) == 1
    assert tgt_snaps[0].name == _SNAP
