from datetime import datetime
from typing import Optional

import pytest

from .lib import (
    Apool,
    AProperties,
    Config,
    Context,
    DatasetDescription,
    Environment,
    Filesystem,
    Host,
    Snapshot,
    SnapshotDescription,
    SnapshotFormat,
    Subcmd,
    TestConfig,
    Zpool,
)


_ZPOOL_A = "foo"
_SNAPSHOT = SnapshotFormat.format_(dt = datetime.now())


@pytest.mark.parametrize("json", (False, True))
@pytest.mark.parametrize("route", (None, "", "localhost", "remotehost", "remotehost/remotehost"))
@Environment(TestConfig(
    zpools = [
        Zpool(name = _ZPOOL_A, aproperties = AProperties.from_defaults(),
            datasets = [
                Filesystem(name = "one", snapshots = [
                    Snapshot(_SNAPSHOT),
                ]),
                Filesystem(name = "two", snapshots = [
                    Snapshot(_SNAPSHOT),
                ]),
            ],
            snapshots = [
                Snapshot(_SNAPSHOT),
            ],
        ),
    ]
))
def test_ls_tree_min(ctx: Context, route: Optional[str], json: bool):
    """
    minimal ls tree test, including root dataset and snapshots
    """

    query = _ZPOOL_A if route is None else f"{route:s}:{_ZPOOL_A:s}"
    json_args = ("-j",) if json else tuple()

    res = ctx.abgleich(Subcmd.ls, *json_args, query)
    res.assert_exitcode(0)

    entries = ctx.parse_ls_tree(res.stdout, json = json)

    datasets = [entry for entry in entries if isinstance(entry, DatasetDescription)]
    snapshots = [entry for entry in entries if isinstance(entry, SnapshotDescription)]

    assert {dataset.path for dataset in datasets} == {"/", "/one", "/two"}

    assert len(snapshots) == 3
    for snapshot in snapshots:
        assert ctx[Host.localhost][_ZPOOL_A].aproperties.matches_snapshot_name(snapshot.snapshot)


@pytest.mark.parametrize("json", (False, True))
@Environment(TestConfig(
    abgleich = Config(
        apools = [
            Apool(alias = f"local_{_ZPOOL_A:s}", root = _ZPOOL_A, user = "root"),
        ]
    ),
    zpools = [
        Zpool(name = _ZPOOL_A, aproperties = AProperties.from_defaults(),
            datasets = [
                Filesystem(name = "one", snapshots = [
                    Snapshot(_SNAPSHOT),
                ]),
                Filesystem(name = "two", snapshots = [
                    Snapshot(_SNAPSHOT),
                ]),
            ],
            snapshots = [
                Snapshot(_SNAPSHOT),
            ],
        ),
    ]
))
def test_ls_tree_alias(ctx: Context, json: bool):
    """
    minimal ls tree test, including root dataset and snapshots, with alias
    """

    query = f"local_{_ZPOOL_A:s}"
    json_args = ("-j",) if json else tuple()

    res = ctx.abgleich(Subcmd.ls, *json_args, query)
    res.assert_exitcode(0)

    entries = ctx.parse_ls_tree(res.stdout, json = json)

    datasets = [entry for entry in entries if isinstance(entry, DatasetDescription)]
    snapshots = [entry for entry in entries if isinstance(entry, SnapshotDescription)]

    assert {dataset.path for dataset in datasets} == {"/", "/one", "/two"}

    assert len(snapshots) == 3
    for snapshot in snapshots:
        assert ctx[Host.localhost][_ZPOOL_A].aproperties.matches_snapshot_name(snapshot.snapshot)


@pytest.mark.parametrize("json", (False, True))
@pytest.mark.parametrize("route", (Host.current_b.to_host_name(), f"remotehost/{Host.current_b.to_host_name():s}"))
@Environment(TestConfig(
    nodes = dict(
        current_b = dict(
            required = True,
            zpools = [
                Zpool(name = _ZPOOL_A, aproperties = AProperties.from_defaults(),
                    datasets = [
                        Filesystem(name = "one", snapshots = [
                            Snapshot(_SNAPSHOT),
                        ]),
                        Filesystem(name = "two", snapshots = [
                            Snapshot(_SNAPSHOT),
                        ]),
                    ],
                    snapshots = [
                        Snapshot(_SNAPSHOT),
                    ],
                ),
            ],
        ),
    ),
))
def test_ls_tree_remote(ctx: Context, route: Optional[str], json: bool):
    """
    minimal ls tree test, including root dataset and snapshots
    """

    query = f"{route:s}:{_ZPOOL_A:s}"
    json_args = ("-j",) if json else tuple()

    res = ctx.abgleich(Subcmd.ls, *json_args, query)
    res.assert_exitcode(0)

    entries = ctx.parse_ls_tree(res.stdout, json = json)

    datasets = [entry for entry in entries if isinstance(entry, DatasetDescription)]
    snapshots = [entry for entry in entries if isinstance(entry, SnapshotDescription)]

    assert {dataset.path for dataset in datasets} == {"/", "/one", "/two"}

    assert len(snapshots) == 3
    for snapshot in snapshots:
        assert ctx[Host.current_b][_ZPOOL_A].aproperties.matches_snapshot_name(snapshot.snapshot)
