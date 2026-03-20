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


@pytest.mark.parametrize("json", (False, True))
@pytest.mark.parametrize("routed", (
    pytest.param(False, id = "via_localhost"),
    pytest.param(True,  id = "via_other_a"),
))
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
def test_sync_route_initial(ctx: Context, routed: bool, json: bool):
    """
    Route shortening test: initial transfer of one child filesystem between other_a and other_b.

    The test is run in two configurations:

    ``via_localhost`` (routed=False)
        Source route is ``other_a``, target route is ``other_b``.  ``--direct``
        is not passed.  The pipe runs on localhost: both SSH processes are wired
        together inside a local ``bash -c 'set -o pipefail; ...'`` wrapper.
        Both host names appear as explicit SSH hops in the command string, and
        the outer command starts with ``bash``, not ``ssh``.

    ``via_other_a`` (routed=True)
        Source route is ``other_a``, target route is ``other_a/other_b``.
        ``--direct`` is passed, enabling route shortening.  The common prefix
        ``other_a`` becomes the entry point: abgleich SSHs into ``other_a`` and
        runs the full pipe there inside ``bash -c 'set -o pipefail; ...'``.  The
        complete command string — including the outer SSH and the shell wrapper
        — is reported to the user, so both host names and ``pipefail`` are
        visible.

    Both configurations must complete successfully and leave the snapshot on
    ``other_b`` while leaving ``other_a`` unchanged.  The command string of the
    ``TransferInitial`` transaction is inspected to confirm which piping
    mechanism was selected.
    """

    other_a = Host.other_a.to_host_name()
    other_b = Host.other_b.to_host_name()

    src = f"{other_a:s}:root%{_ZPOOL_SRC:s}"
    if routed:
        # Target route shares other_a as its leading hop with the source route.
        # abgleich will SSH into other_a and execute the pipe there inside a
        # bash -c wrapper; the complete command string, including that outer SSH
        # call, is reported to the user.
        tgt = f"{other_a:s}/{other_b:s}:root%{_ZPOOL_TGT:s}"
    else:
        # No common prefix: the pipe runs on localhost, both sides require an
        # explicit SSH call.
        tgt = f"{other_b:s}:root%{_ZPOOL_TGT:s}"
    json_args = ("-j",) if json else tuple()
    direct_args = ("-d",) if routed else tuple()

    res = ctx.abgleich(Subcmd.sync, *json_args, *direct_args, "-y", src, tgt)
    res.assert_exitcode(0)

    transactions = ctx.parse_transactions(res.stdout, json = json)

    assert len(transactions) == 1
    assert isinstance(transactions[0], TransferInitialTransaction)
    assert transactions[0].dataset == "/one"
    assert transactions[0].snapshot == _SNAP

    # Inspect the command string to verify the correct piping mechanism was used.
    #
    # CommandChain::to_string() always emits the complete command the user will
    # see — including the outer SSH and shell wrapper when an entry route is in
    # effect.  Under the bash-everything approach every multi-stage chain is
    # wrapped in `bash -c 'set -o pipefail; ...'`, so "pipefail" is present in
    # both configurations.  The clean differentiator is instead whether the
    # outer command starts with `ssh <entry_host>` (direct mode, routed) or
    # `bash` (non-direct mode, local).  In both cases all relevant host names
    # are visible in the command string.
    cmd = transactions[0].command
    if routed:
        assert cmd.startswith(f"ssh {other_a}"), (
            f"routed transfer must use {other_a!r} as the outer SSH entry point, "
            f"but command starts differently: {cmd!r}"
        )
        assert "pipefail" in cmd, (
            f"routed transfer must include 'set -o pipefail' in the remote bash wrapper: {cmd!r}"
        )
        assert other_b in cmd, (
            f"target hop {other_b!r} must appear inside the remote pipe command: {cmd!r}"
        )
    else:
        assert cmd.startswith("bash"), (
            f"non-direct transfer must use a local bash wrapper, "
            f"but command starts differently: {cmd!r}"
        )
        assert "pipefail" in cmd, (
            f"non-direct transfer must include 'set -o pipefail' in the local bash wrapper: {cmd!r}"
        )
        assert other_a in cmd, (
            f"without route shortening {other_a!r} must appear as an explicit SSH hop: {cmd!r}"
        )
        assert other_b in cmd, (
            f"without route shortening {other_b!r} must appear as an explicit SSH hop: {cmd!r}"
        )

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
@pytest.mark.parametrize("routed", (
    pytest.param(False, id = "via_localhost"),
    pytest.param(True,  id = "via_other_a"),
))
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
def test_sync_route_incremental(ctx: Context, routed: bool, json: bool):
    """
    Route shortening test: incremental transfer of one child filesystem between other_a and other_b.

    The test is run in the same two route configurations as
    ``test_sync_route_initial``; see that test for the per-permutation details.

    Step 1 – initial sync: transfers ``_SNAP`` to the target (TransferInitial).
    Step 2 – snap: creates a second snapshot (``snap_b``) on the source child.
    Step 3 – incremental sync: transfers ``snap_b`` to the target (TransferIncremental).

    The command string of the ``TransferIncremental`` transaction produced in
    step 3 is inspected (in JSON mode) to confirm which piping mechanism was
    selected.

    Design note
    -----------
    The source root carries ``snap=never`` so that step 2 only snapshots the
    child dataset, keeping the transaction count predictable.  ``snap_b`` is
    created via ``abgleich snap`` rather than the test infrastructure so that
    the snapshot's ZFS creation timestamp is preserved across the initial
    transfer, satisfying the common-snapshot equality check in the sync engine.
    """

    other_a = Host.other_a.to_host_name()
    other_b = Host.other_b.to_host_name()

    src = f"{other_a:s}:root%{_ZPOOL_SRC:s}"
    if routed:
        tgt = f"{other_a:s}/{other_b:s}:root%{_ZPOOL_TGT:s}"
    else:
        tgt = f"{other_b:s}:root%{_ZPOOL_TGT:s}"
    json_args = ("-j",) if json else tuple()
    direct_args = ("-d",) if routed else tuple()

    # step 1: initial sync — transfers _SNAP from source child to target
    res_sync1 = ctx.abgleich(Subcmd.sync, *json_args, *direct_args, "-y", src, tgt)
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
    res_sync2 = ctx.abgleich(Subcmd.sync, *json_args, *direct_args, "-y", src, tgt)
    res_sync2.assert_exitcode(0)

    transactions = ctx.parse_transactions(res_sync2.stdout, json = json)
    assert len(transactions) == 1
    assert isinstance(transactions[0], TransferIncrementalTransaction)
    assert transactions[0].dataset == "/one"
    assert transactions[0].from_snapshot == _SNAP
    assert transactions[0].to_snapshot == snap_b

    # Inspect the command string of the incremental transfer.
    # See test_sync_route_initial for the rationale: "pipefail" is now always
    # present; the outer `ssh <entry_host>` vs `bash` prefix is the differentiator.
    cmd = transactions[0].command
    if routed:
        assert cmd.startswith(f"ssh {other_a}"), (
            f"routed transfer must use {other_a!r} as the outer SSH entry point, "
            f"but command starts differently: {cmd!r}"
        )
        assert "pipefail" in cmd, (
            f"routed transfer must include 'set -o pipefail' in the remote bash wrapper: {cmd!r}"
        )
        assert other_b in cmd, (
            f"target hop {other_b!r} must appear inside the remote pipe command: {cmd!r}"
        )
    else:
        assert cmd.startswith("bash"), (
            f"non-direct transfer must use a local bash wrapper, "
            f"but command starts differently: {cmd!r}"
        )
        assert "pipefail" in cmd, (
            f"non-direct transfer must include 'set -o pipefail' in the local bash wrapper: {cmd!r}"
        )
        assert other_a in cmd, (
            f"without route shortening {other_a!r} must appear as an explicit SSH hop: {cmd!r}"
        )
        assert other_b in cmd, (
            f"without route shortening {other_b!r} must appear as an explicit SSH hop: {cmd!r}"
        )

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
