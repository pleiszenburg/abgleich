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
def test_sync_compress_initial(ctx: Context, json: bool):
    """
    ``abgleich sync -x`` pipes ``zfs send`` (without ``-c``) through ``xz -5``
    on the sending host and ``xz -d`` on the receiving host.  The ``-c`` flag
    is suppressed because sending pre-compressed blocks would reduce xz
    efficiency.

    Source carries one child dataset with one snapshot.  After a compressed
    sync the snapshot must be present on the target, proving that the xz |
    xz -d round-trip preserved the stream correctly.

    Requires ``xz`` to be installed on both source and target hosts.
    """

    src = f"root%{_ZPOOL_SRC:s}"
    tgt = f"root%{_ZPOOL_TGT:s}"
    json_args = ("-j",) if json else tuple()

    res = ctx.abgleich(Subcmd.sync, *json_args, "-x", "-y", src, tgt)
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

    src_snaps = list((ctx[Host.localhost][_ZPOOL_SRC] / "one").snapshots)
    assert len(src_snaps) == 1
    assert src_snaps[0].name == _SNAP


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
def test_sync_compress_incremental(ctx: Context, json: bool):
    """
    ``abgleich sync -x`` also works for incremental transfers (without ``-c``).

    After an initial sync a second snapshot is created by ``abgleich snap``.
    A compressed incremental sync must transfer the new snapshot via xz,
    leaving both snapshots on the target.
    """

    src = f"root%{_ZPOOL_SRC:s}"
    tgt = f"root%{_ZPOOL_TGT:s}"
    json_args = ("-j",) if json else tuple()

    # Initial compressed sync.
    res_sync1 = ctx.abgleich(Subcmd.sync, *json_args, "-x", "-y", src, tgt)
    res_sync1.assert_exitcode(0)

    transactions = ctx.parse_transactions(res_sync1.stdout, json = json)
    assert len(transactions) == 1
    assert isinstance(transactions[0], TransferInitialTransaction)

    ctx.reload()

    # Create a second snapshot on the source.
    res_snap = ctx.abgleich(Subcmd.snap, *json_args, "-y", src)
    res_snap.assert_exitcode(0)

    ctx.reload()

    # Incremental compressed sync.
    res_sync2 = ctx.abgleich(Subcmd.sync, *json_args, "-x", "-y", src, tgt)
    res_sync2.assert_exitcode(0)

    transactions2 = ctx.parse_transactions(res_sync2.stdout, json = json)
    assert len(transactions2) == 1
    assert isinstance(transactions2[0], TransferIncrementalTransaction)
    assert transactions2[0].dataset == "/one"

    ctx.reload()

    tgt_snaps = list((ctx[Host.localhost][_ZPOOL_TGT] / "one").snapshots)
    assert len(tgt_snaps) == 2
