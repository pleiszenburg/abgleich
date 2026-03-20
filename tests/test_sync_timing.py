from time import time

import pytest

from .lib import (
    AProperties,
    # Command,
    Context,
    CreateSnapshotTransaction,
    Environment,
    Filesystem,
    Host,
    Path,
    Snap,
    Subcmd,
    TestConfig,
    TransferInitialTransaction,
    Zpool,
)


_ZPOOL_SRC = "src"
_ZPOOL_TGT = "tgt"


@pytest.mark.skip(reason="hardware-specific, for debugging only")
@pytest.mark.parametrize("rate", (False, True))
@pytest.mark.parametrize("xz", (False, True))
@Environment(TestConfig(
    zpools = [
        Zpool(
            name = _ZPOOL_SRC,
            aproperties = AProperties.from_defaults(snap = Snap.never),
            compression = False,
            datasets = [
                Filesystem(
                    name = "one",
                    aproperties = AProperties.from_defaults(snap = Snap.changed),
                ),
            ],
        ),
        Zpool(
            name = _ZPOOL_TGT,
            compression = False,
        ),
    ],
))
def test_sync_timing(ctx: Context, rate: bool, xz: bool):
    """
    Test rate limits and compression combined
    """

    if rate and not xz:
        print("Skip slow")
        return

    src = f"root%{_ZPOOL_SRC:s}"
    tgt = f"root%{_ZPOOL_TGT:s}"
    rate_args = ("-r", "16k") if rate else tuple()
    xz_args = ("-x", "1") if xz else tuple()

    _ = (Path(
        (ctx[Host.localhost][_ZPOOL_SRC] / "one").mountpoint_abs
    ) / "data.bin").compressible(Host.localhost, size = 5 * 1024 ** 2)  # 5 MByte

    res = ctx.abgleich(Subcmd.snap, "-y", src)
    res.assert_exitcode(0)

    transactions = ctx.parse_transactions(res.stdout, json = False)
    assert len(transactions) == 1  # transactions / new snapshots
    assert isinstance(transactions[0], CreateSnapshotTransaction)
    snapshot_name = transactions[0].snapshot

    ctx.reload()

    start = time()

    res = ctx.abgleich(Subcmd.sync, *rate_args, *xz_args, "-y", src, tgt)
    res.assert_exitcode(0)

    duration = time() - start

    print("Rate", rate, "Xz", xz, "Duration", duration)

    transactions = ctx.parse_transactions(res.stdout, json = False)
    assert len(transactions) == 1
    assert isinstance(transactions[0], TransferInitialTransaction)
    assert transactions[0].dataset == "/one"
    assert transactions[0].snapshot == snapshot_name

    ctx.reload()

    tgt_snaps = list((ctx[Host.localhost][_ZPOOL_TGT] / "one").snapshots)
    assert len(tgt_snaps) == 1
    assert tgt_snaps[0].name == snapshot_name
