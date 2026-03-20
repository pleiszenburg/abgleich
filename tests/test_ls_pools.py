from typing import Optional

import pytest

from .lib import (
    Apool,
    AProperties,
    Config,
    Context,
    Environment,
    Filesystem,
    Host,
    Subcmd,
    TestConfig,
    Zpool,
)


_ZPOOL_A = "foo"
_ZPOOL_B = "bar"


@pytest.mark.parametrize("json", (False, True))
@pytest.mark.parametrize("route", (None, "", "localhost", "remotehost", "remotehost/remotehost"))
@Environment(TestConfig(
    abgleich = Config(
        apools = [
            Apool(alias = f"local_{_ZPOOL_A:s}", root = _ZPOOL_A),
        ]
    ),
    zpools = [
        Zpool(name = _ZPOOL_A, aproperties = AProperties.from_defaults(), datasets = [
            Filesystem(name = "one"),
            Filesystem(name = "two"),
        ]),
        Zpool(name = _ZPOOL_B, datasets = [
            Filesystem(name = "three"),
            Filesystem(name = "four"),
        ]),
    ]
))
def test_ls_pools_min(ctx: Context, route: Optional[str], json: bool):
    """
    minimal list of pools
    """

    query_args = tuple() if route is None else (f"{route:s}:",)
    json_args = ("-j",) if json else tuple()

    res = ctx.abgleich(Subcmd.ls, *json_args, *query_args)
    res.assert_exitcode(0)

    apools = ctx.parse_ls_pools(res.stdout, json=json)

    roots = [apool.root.split("/")[0] for apool in apools]
    assert len(roots) == len(set(roots))
    assert set(roots) == ctx[Host.localhost].get_ondisk_zpool_names()

    aliases = [apool.alias for apool in apools if apool.alias is not None]
    assert len(aliases) == len(set(aliases))

    if route in (None, "", "localhost"):
        assert set(aliases) == set(ctx.config.aliases)
    else:
        assert aliases == []
