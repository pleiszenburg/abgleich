from datetime import datetime

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

_NC_PORT = 18432


@pytest.mark.parametrize("json", (False, True))
@pytest.mark.parametrize("insecure", (False, True))
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
def test_sync_insecure_initial(ctx: Context, insecure: bool, json: bool):
    """
    initial sync via insecure (nc) or secure (SSH) transfer, controlled by insecure

    insecure=True  – passes --insecure HOST:PORT; data flows via netcat, bypassing SSH.
               The rendered transaction command must contain 'nc'.
    insecure=False – normal SSH-based push; 'nc' must NOT appear in the command.

    Both variants must transfer the snapshot to the target and leave the source
    unchanged.
    """

    src = f"{Host.localhost.to_host_name():s}:root%{_ZPOOL_SRC:s}"
    tgt = f"{Host.current_b.to_host_name():s}:root%{_ZPOOL_TGT:s}"
    json_args = ("-j",) if json else tuple()
    insecure_args = ("--insecure", f"{Host.current_b.to_host_name():s}:{_NC_PORT}") if insecure else tuple()

    res = ctx.abgleich(Subcmd.sync, *json_args, "-y", *insecure_args, src, tgt)
    res.assert_exitcode(0)

    transactions = ctx.parse_transactions(res.stdout, json = json)

    assert len(transactions) == 1
    assert isinstance(transactions[0], TransferInitialTransaction)
    assert transactions[0].dataset == "/one"
    assert transactions[0].snapshot == _SNAP

    if insecure:
        assert "nc" in transactions[0].command, (
            f"expected 'nc' in insecure transfer command; got: {transactions[0].command!r}"
        )
    else:
        assert "nc" not in transactions[0].command, (
            f"unexpected 'nc' in secure transfer command; got: {transactions[0].command!r}"
        )

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
@pytest.mark.parametrize("insecure", (False, True))
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
def test_sync_insecure_incremental(ctx: Context, insecure: bool, json: bool):
    """
    incremental sync via insecure (nc) or secure (SSH) transfer, controlled by insecure

    insecure=True  – both sync steps use --insecure HOST:PORT; 'nc' must appear in each
               rendered transfer command.
    insecure=False – normal SSH-based push; 'nc' must NOT appear in any command.

    Step 1 – initial sync: transfers _SNAP (TransferInitial).
    Step 2 – snap: creates snap_b on the source child dataset.
    Step 3 – incremental sync: transfers snap_b (TransferIncremental).

    After step 3 the target must carry both snapshots; the source is unchanged.

    Design notes
    ------------
    The source root is configured with snap=never so step 2 only touches the
    child dataset, keeping transaction counts predictable.

    snap_b is created via 'abgleich snap' so that the creation timestamp on the
    target copy of _SNAP matches the source (zfs receive preserves it), which is
    required by the common-snapshot equality check inside the sync engine.
    """

    src = f"{Host.localhost.to_host_name():s}:root%{_ZPOOL_SRC:s}"
    tgt = f"{Host.current_b.to_host_name():s}:root%{_ZPOOL_TGT:s}"
    json_args = ("-j",) if json else tuple()
    insecure_args = ("--insecure", f"{Host.current_b.to_host_name():s}:{_NC_PORT}") if insecure else tuple()

    # step 1: initial sync — transfers _SNAP from source child to target
    res_sync1 = ctx.abgleich(Subcmd.sync, *json_args, "-y", *insecure_args, src, tgt)
    res_sync1.assert_exitcode(0)

    transactions = ctx.parse_transactions(res_sync1.stdout, json = json)
    assert len(transactions) == 1
    assert isinstance(transactions[0], TransferInitialTransaction)
    assert transactions[0].dataset == "/one"
    assert transactions[0].snapshot == _SNAP

    if insecure:
        assert "nc" in transactions[0].command, (
            f"expected 'nc' in insecure initial transfer command; got: {transactions[0].command!r}"
        )
    else:
        assert "nc" not in transactions[0].command, (
            f"unexpected 'nc' in secure initial transfer command; got: {transactions[0].command!r}"
        )

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
    res_sync2 = ctx.abgleich(Subcmd.sync, *json_args, "-y", *insecure_args, src, tgt)
    res_sync2.assert_exitcode(0)

    transactions = ctx.parse_transactions(res_sync2.stdout, json = json)
    assert len(transactions) == 1
    assert isinstance(transactions[0], TransferIncrementalTransaction)
    assert transactions[0].dataset == "/one"
    assert transactions[0].from_snapshot == _SNAP
    assert transactions[0].to_snapshot == snap_b

    if insecure:
        assert "nc" in transactions[0].command, (
            f"expected 'nc' in insecure incremental transfer command; got: {transactions[0].command!r}"
        )
    else:
        assert "nc" not in transactions[0].command, (
            f"unexpected 'nc' in secure incremental transfer command; got: {transactions[0].command!r}"
        )

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
