import pytest

from .lib import (
    Apool,
    AProperties,
    Config,
    Context,
    Environment,
    Filesystem,
    MntLocal,
    Snap,
    Snapshot,
    TestConfig,
    Volume,
    Zpool,
)


_ZPOOL_A = "foo"
_ZPOOL_B = "bar"


@pytest.mark.skip(reason="test template")
@Environment(TestConfig(
    abgleich = Config(
        apools = [
            Apool(alias = f"local_{_ZPOOL_A:s}", root = _ZPOOL_A),
            Apool(alias = f"local_{_ZPOOL_B:s}", root = _ZPOOL_B),
        ]
    ),
    zpools = [
        Zpool(name = _ZPOOL_A, aproperties = AProperties.from_defaults(), datasets = [
            Filesystem(name = "one", mountpoint = MntLocal(None), aproperties = AProperties(snap = Snap.never)),
            Filesystem(name = "two", snapshots = [
                Snapshot(name = "backup_a"),
                Snapshot(name = "backup_b"),
            ]),
            Volume(name = "baz", size = 20 * 1024**2, sparse = True),
        ]),
        Zpool(name = _ZPOOL_B, mountpoint = MntLocal(None)),
    ]
))
def test_base_min(ctx: Context):
    """
    minimal test template
    """

    ctx.shell()
    ctx.reload()
    ctx.shell()
