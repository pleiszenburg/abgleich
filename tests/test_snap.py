from datetime import datetime
from typing import Optional
import os

import pytest

from .lib import (
    Apool,
    AProperties,
    CreateSnapshotTransaction,
    Config,
    Context,
    Environment,
    Filesystem,
    Host,
    Path,
    Platform,
    Snap,
    Snapshot,
    SnapshotFormat,
    Subcmd,
    TestConfig,
    Zpool,
)


_ZPOOL_A = "foo"
_ZPOOL_B = "bar"
_SNAP = SnapshotFormat.format_(dt = datetime.now())
_FN = "stuff"


@pytest.mark.parametrize("json", (False, True))
@pytest.mark.parametrize("route", (None, "", "localhost"))
@Environment(TestConfig(
    zpools = [
        Zpool(
            name = _ZPOOL_A,
            aproperties = AProperties.from_defaults(),
            datasets = [
                Filesystem(name = "one"),
            ],
        ),
        Zpool(
            name = _ZPOOL_B,
            datasets = [
                Filesystem(name = "two"),
            ],
        ),
    ]
))
def test_snap_min_local(ctx: Context, route: Optional[str], json: bool):
    """
    minimal snap test, no alias, including root dataset, locally

    Two zpools, only one targeted specifically by abgleich.
    The second zpool must remain unchanged.
    """

    zpool = f'root%{_ZPOOL_A:s}'
    query = zpool if route is None else f"{route:s}:{zpool:s}"
    json_args = ("-j",) if json else tuple()

    res = ctx.abgleich(Subcmd.snap, *json_args, "-y", query)  # yes to all
    res.assert_exitcode(0)

    transactions = ctx.parse_transactions(res.stdout, json = json)

    assert len(transactions) == 2  # transactions / new snapshots
    assert all(isinstance(transaction, CreateSnapshotTransaction) for transaction in transactions)

    assert {transaction.dataset for transaction in transactions} == {"/", "/one"}

    for transaction in transactions:
        assert ctx[Host.localhost][_ZPOOL_A].aproperties.matches_snapshot_name(transaction.snapshot)

    ctx.reload()

    root_snaps = set(ctx[Host.localhost][_ZPOOL_A].snapshots)
    assert len(root_snaps) == 1  # new
    assert ctx[Host.localhost][_ZPOOL_A].aproperties.matches_snapshot_name(root_snaps.pop().name)

    one_snaps = set((ctx[Host.localhost][_ZPOOL_A] / "one").snapshots)
    assert len(one_snaps) == 1  # new
    assert ctx[Host.localhost][_ZPOOL_A].aproperties.matches_snapshot_name(one_snaps.pop().name)

    assert len(set(ctx[Host.localhost][_ZPOOL_B].snapshots)) == 0  # nothing
    assert len(set((ctx[Host.localhost][_ZPOOL_B] / "two").snapshots)) == 0  # nothing


@pytest.mark.parametrize("json", (False, True))
@Environment(TestConfig(
    abgleich = Config(
        apools = [
            Apool(alias = f"local_{_ZPOOL_A:s}", user = "root", root = _ZPOOL_A),
        ]
    ),
    zpools = [
        Zpool(
            name = _ZPOOL_A,
            aproperties = AProperties.from_defaults(),
            datasets = [
                Filesystem(name = "one"),
            ],
        ),
        Zpool(
            name = _ZPOOL_B,
            datasets = [
                Filesystem(name = "two"),
            ],
        ),
    ]
))
def test_snap_min_alias_local(ctx: Context, json: bool):
    """
    minimal snap test, with alias, including root dataset, locally

    Two zpools, only one targeted specifically by abgleich.
    The second zpool must remain unchanged.
    """

    query = f"local_{_ZPOOL_A:s}"
    json_args = ("-j",) if json else tuple()

    res = ctx.abgleich(Subcmd.snap, *json_args, "-y", query)  # yes to all
    res.assert_exitcode(0)

    transactions = ctx.parse_transactions(res.stdout, json = json)

    assert len(transactions) == 2  # transactions / new snapshots
    assert all(isinstance(transaction, CreateSnapshotTransaction) for transaction in transactions)

    assert {transaction.dataset for transaction in transactions} == {"/", "/one"}

    for transaction in transactions:
        assert ctx[Host.localhost][_ZPOOL_A].aproperties.matches_snapshot_name(transaction.snapshot)

    ctx.reload()

    root_snaps = set(ctx[Host.localhost][_ZPOOL_A].snapshots)
    assert len(root_snaps) == 1  # new
    assert ctx[Host.localhost][_ZPOOL_A].aproperties.matches_snapshot_name(root_snaps.pop().name)

    one_snaps = set((ctx[Host.localhost][_ZPOOL_A] / "one").snapshots)
    assert len(one_snaps) == 1  # new
    assert ctx[Host.localhost][_ZPOOL_A].aproperties.matches_snapshot_name(one_snaps.pop().name)

    assert len(set(ctx[Host.localhost][_ZPOOL_B].snapshots)) == 0  # nothing
    assert len(set((ctx[Host.localhost][_ZPOOL_B] / "two").snapshots)) == 0  # nothing


@pytest.mark.parametrize("json", (False, True))
@pytest.mark.parametrize("route", (
    Host.current_b.to_host_name(),
    f"remotehost/{Host.current_b.to_host_name():s}",
))
@Environment(TestConfig(
    nodes = dict(
        current_b = dict(
            required = True,
            zpools = [
                Zpool(
                    name = _ZPOOL_A,
                    aproperties = AProperties.from_defaults(),
                    datasets = [
                        Filesystem(name = "one"),
                    ],
                ),
                Zpool(
                    name = _ZPOOL_B,
                    datasets = [
                        Filesystem(name = "two"),
                    ],
                ),
            ]
        ),
    ),
))
def test_snap_min_remote(ctx: Context, route: str, json: bool):
    """
    minimal snap test, no alias, including root dataset, remote host

    Two zpools, only one targeted specifically by abgleich.
    The second zpool must remain unchanged.
    """

    zpool = f'root%{_ZPOOL_A:s}'
    query = f"{route:s}:{zpool:s}"
    json_args = ("-j",) if json else tuple()

    res = ctx.abgleich(Subcmd.snap, *json_args, "-y", query)  # yes to all
    res.assert_exitcode(0)

    transactions = ctx.parse_transactions(res.stdout, json = json)

    assert len(transactions) == 2  # transactions / new snapshots
    assert all(isinstance(transaction, CreateSnapshotTransaction) for transaction in transactions)

    assert {transaction.dataset for transaction in transactions} == {"/", "/one"}

    for transaction in transactions:
        assert ctx[Host.current_b][_ZPOOL_A].aproperties.matches_snapshot_name(transaction.snapshot)

    ctx.reload()

    root_snaps = set(ctx[Host.current_b][_ZPOOL_A].snapshots)
    assert len(root_snaps) == 1  # new
    assert ctx[Host.current_b][_ZPOOL_A].aproperties.matches_snapshot_name(root_snaps.pop().name)

    one_snaps = set((ctx[Host.current_b][_ZPOOL_A] / "one").snapshots)
    assert len(one_snaps) == 1  # new
    assert ctx[Host.current_b][_ZPOOL_A].aproperties.matches_snapshot_name(one_snaps.pop().name)

    assert len(set(ctx[Host.current_b][_ZPOOL_B].snapshots)) == 0  # nothing
    assert len(set((ctx[Host.current_b][_ZPOOL_B] / "two").snapshots)) == 0  # nothing


@pytest.mark.parametrize("json", (False, True))
@Environment(TestConfig(
    zpools = [
        Zpool(
            name = _ZPOOL_A,
            aproperties = None,
            datasets = [
                Filesystem(name = "one"),
            ],
        ),
        Zpool(
            name = _ZPOOL_B,
            datasets = [
                Filesystem(name = "two"),
            ],
        ),
    ]
))
def test_snap_implicit_defaults(ctx: Context, json: bool):
    """
    just like test_snap_min, but no defaults set on dataset
    """

    zpool = f'root%{_ZPOOL_A:s}'
    query = zpool
    json_args = ("-j",) if json else tuple()

    res = ctx.abgleich(Subcmd.snap, *json_args, "-y", query)  # yes to all
    res.assert_exitcode(0)

    transactions = ctx.parse_transactions(res.stdout, json = json)

    assert len(transactions) == 2  # transactions / new snapshots
    assert all(isinstance(transaction, CreateSnapshotTransaction) for transaction in transactions)

    assert {transaction.dataset for transaction in transactions} == {"/", "/one"}

    for transaction in transactions:
        assert ctx[Host.localhost][_ZPOOL_A].aproperties.matches_snapshot_name(transaction.snapshot)

    ctx.reload()

    root_snaps = set(ctx[Host.localhost][_ZPOOL_A].snapshots)
    assert len(root_snaps) == 1  # new
    assert ctx[Host.localhost][_ZPOOL_A].aproperties.matches_snapshot_name(root_snaps.pop().name)

    one_snaps = set((ctx[Host.localhost][_ZPOOL_A] / "one").snapshots)
    assert len(one_snaps) == 1  # new
    assert ctx[Host.localhost][_ZPOOL_A].aproperties.matches_snapshot_name(one_snaps.pop().name)

    assert len(set(ctx[Host.localhost][_ZPOOL_B].snapshots)) == 0  # nothing
    assert len(set((ctx[Host.localhost][_ZPOOL_B] / "two").snapshots)) == 0  # nothing


@pytest.mark.parametrize("json", (False, True))
@Environment(*(TestConfig(
    zpools = [
        Zpool(
            name = _ZPOOL_A,
            aproperties = AProperties.from_defaults(),
            datasets = [
                Filesystem(
                    name = "one",
                    aproperties = aproperties,
                ),
            ],
        ),
        Zpool(
            name = _ZPOOL_B,
            datasets = [
                Filesystem(name = "two"),
            ],
        ),
    ],
) for aproperties in (
    AProperties.from_defaults(),
    AProperties(snap = Snap.never),  # tested feature
)))
def test_snap_suppress_without_initial_snapshot(ctx: Context, json: bool):
    """
    prevent snapshot if there is no previous snapshot
    """

    feature = (ctx[Host.localhost][_ZPOOL_A] / "one").aproperties.snap is Snap.never

    zpool = f'root%{_ZPOOL_A:s}'
    query = zpool
    json_args = ("-j",) if json else tuple()

    res = ctx.abgleich(Subcmd.snap, *json_args, "-y", query)  # yes to all
    res.assert_exitcode(0)

    transactions = ctx.parse_transactions(res.stdout, json = json)

    assert len(transactions) == (1 if feature else 2)  # transactions / new snapshots
    assert all(isinstance(transaction, CreateSnapshotTransaction) for transaction in transactions)

    assert {transaction.dataset for transaction in transactions} == ({"/"} if feature else {"/", "/one"})

    for transaction in transactions:
        assert ctx[Host.localhost][_ZPOOL_A].aproperties.matches_snapshot_name(transaction.snapshot)

    ctx.reload()

    root_snaps = set(ctx[Host.localhost][_ZPOOL_A].snapshots)
    assert len(root_snaps) == 1  # new
    assert ctx[Host.localhost][_ZPOOL_A].aproperties.matches_snapshot_name(root_snaps.pop().name)

    if feature:
        assert len(set((ctx[Host.localhost][_ZPOOL_A] / "one").snapshots)) == 0
    else:
        one_snaps = set((ctx[Host.localhost][_ZPOOL_A] / "one").snapshots)
        assert len(one_snaps) == 1  # new
        assert ctx[Host.localhost][_ZPOOL_A].aproperties.matches_snapshot_name(one_snaps.pop().name)

    assert len(set(ctx[Host.localhost][_ZPOOL_B].snapshots)) == 0  # nothing
    assert len(set((ctx[Host.localhost][_ZPOOL_B] / "two").snapshots)) == 0  # nothing


@pytest.mark.parametrize("json", (False, True))
@Environment(*(TestConfig(
    zpools = [
        Zpool(
            name = _ZPOOL_A,
            aproperties = AProperties.from_defaults(),
            snapshots = [
                Snapshot(_SNAP),
            ],
            datasets = [
                Filesystem(
                    name = "one",
                    aproperties = aproperties,
                    snapshots = [
                        Snapshot(_SNAP),
                    ],
                ),
            ],
        ),
        Zpool(name = _ZPOOL_B, datasets = [
            Filesystem(name = "two"),
        ]),
    ],
) for aproperties in (
    AProperties.from_defaults(),
    AProperties(snap = Snap.never),  # tested feature
)))
def test_snap_suppress_with_initial_snapshot(ctx: Context, json: bool):
    """
    prevent snapshot if there is one previous snapshot and subsequent changes
    """

    feature = (ctx[Host.localhost][_ZPOOL_A] / "one").aproperties.snap is Snap.never

    Path(os.path.join(ctx[Host.localhost][_ZPOOL_A].mountpoint_abs, _FN)).randomize(host = Host.localhost, count = 15)
    Path(os.path.join((ctx[Host.localhost][_ZPOOL_A] / "one").mountpoint_abs, _FN)).randomize(host = Host.localhost, count = 15)

    zpool = f'root%{_ZPOOL_A:s}'
    query = zpool
    json_args = ("-j",) if json else tuple()

    res = ctx.abgleich(Subcmd.snap, *json_args, "-y", query)  # yes to all
    res.assert_exitcode(0)

    transactions = ctx.parse_transactions(res.stdout, json = json)

    assert len(transactions) == (1 if feature else 2) # transactions / new snapshots
    assert all(isinstance(transaction, CreateSnapshotTransaction) for transaction in transactions)

    assert {transaction.dataset for transaction in transactions} == ({"/"} if feature else {"/", "/one"})

    for transaction in transactions:
        assert ctx[Host.localhost][_ZPOOL_A].aproperties.matches_snapshot_name(transaction.snapshot)

    ctx.reload()

    root_snaps = set(ctx[Host.localhost][_ZPOOL_A].snapshots)
    assert len(root_snaps) == 2
    root_snaps -= {Snapshot(_SNAP)}
    assert len(root_snaps) == 1
    assert ctx[Host.localhost][_ZPOOL_A].aproperties.matches_snapshot_name(root_snaps.pop().name)

    one_snaps = set((ctx[Host.localhost][_ZPOOL_A] / "one").snapshots)
    assert len(one_snaps) == (1 if feature else 2)
    one_snaps -= {Snapshot(_SNAP)}
    assert len(one_snaps) == (0 if feature else 1)
    if not feature:
        assert ctx[Host.localhost][_ZPOOL_A].aproperties.matches_snapshot_name(one_snaps.pop().name)

    assert len(set(ctx[Host.localhost][_ZPOOL_B].snapshots)) == 0  # nothing
    assert len(set((ctx[Host.localhost][_ZPOOL_B] / "two").snapshots)) == 0  # nothing


@pytest.mark.skipif(Platform.current is Platform.freebsd, reason = "See https://github.com/openzfs/zfs/issues/18325")
@pytest.mark.parametrize("json", (False, True))
@Environment(*(TestConfig(
    zpools = [
        Zpool(
            name = _ZPOOL_A,
            aproperties = AProperties.from_defaults(),
            snapshots = [
                Snapshot(_SNAP),
            ],
            datasets = [
                Filesystem(
                    name = "one",
                    aproperties = aproperties,
                    snapshots = [
                        Snapshot(_SNAP),
                    ],
                ),
            ],
        ),
        Zpool(name = _ZPOOL_B, datasets = [
            Filesystem(name = "two"),
        ]),
    ],
) for aproperties in (
    AProperties.from_defaults(),
    AProperties(threshold = 0),  # tested feature
)))
def test_snap_threshold_with_initial_snapshot(ctx: Context, json: bool):
    """
    check threshold behaviour on filesystem
    """

    feature = (ctx[Host.localhost][_ZPOOL_A] / "one").aproperties.threshold == 0

    _ = Path((ctx[Host.localhost][_ZPOOL_A] / "one").mountpoint_abs).listdir(Host.localhost)  # force atime change
    ctx[Host.localhost].sync()  # flush changes to make sure test words deterministically

    zpool = f'root%{_ZPOOL_A:s}'
    query = zpool
    json_args = ("-j",) if json else tuple()

    res = ctx.abgleich(Subcmd.snap, *json_args, "-y", query)  # yes to all
    res.assert_exitcode(0)

    ctx.reload()

    transactions = ctx.parse_transactions(res.stdout, json = json)

    assert len(transactions) == (1 if feature else 0) # transactions / new snapshots
    assert all(isinstance(transaction, CreateSnapshotTransaction) for transaction in transactions)

    assert {transaction.dataset for transaction in transactions} == ({"/one"} if feature else set())

    for transaction in transactions:
        assert ctx[Host.localhost][_ZPOOL_A].aproperties.matches_snapshot_name(transaction.snapshot)

    root_snaps = set(ctx[Host.localhost][_ZPOOL_A].snapshots)
    assert root_snaps == {Snapshot(_SNAP)}

    one_snaps = set((ctx[Host.localhost][_ZPOOL_A] / "one").snapshots)
    assert len(one_snaps) == (2 if feature else 1)
    one_snaps -= {Snapshot(_SNAP)}
    assert len(one_snaps) == (1 if feature else 0)
    if feature:
        assert ctx[Host.localhost][_ZPOOL_A].aproperties.matches_snapshot_name(one_snaps.pop().name)

    assert len(set(ctx[Host.localhost][_ZPOOL_B].snapshots)) == 0  # nothing
    assert len(set((ctx[Host.localhost][_ZPOOL_B] / "two").snapshots)) == 0  # nothing


# TODO check if written > threshold, no diff is performed
# TODO check "if volume, no diff etc, snapshot is directly taken"
