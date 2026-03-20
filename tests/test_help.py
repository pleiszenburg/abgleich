import os

import pytest
from tomlkit import parse

from .lib import (
    Context,
    Environment,
    Subcmd,
    NAME,
)


@pytest.mark.parametrize("subcmd", Subcmd.all())
@Environment()
def test_help_base(ctx: Context, subcmd: Subcmd):
    """
    look for command help
    """

    res = ctx.abgleich(subcmd, "--help")

    res.assert_exitcode(0)
    assert all(word in res.stdout for word in (b"Usage", b"Options"))


@Environment()
def test_help_version_param(ctx: Context):
    """
    look for command version
    """

    res = ctx.abgleich(Subcmd.none, "--version")

    with open(os.path.join(f"{NAME:s}-lib", "Cargo.toml"), mode = "r", encoding = "utf-8") as f:
        version = parse(f.read())["package"]["version"]

    res.assert_exitcode(0)
    assert res.stdout.decode("utf-8").strip().split("\n")[-1].strip() == f"{NAME:s} {version:s}"


@Environment()
def test_help_inventory(ctx: Context):
    """
    reverse self-test on sub-command inventory coverage
    """

    expected = {subcmd.to_cli() for subcmd in Subcmd if subcmd is not Subcmd.none}
    expected.add("help")

    res = ctx.abgleich(Subcmd.none, "--help")

    res.assert_exitcode(0)

    lines = res.stdout.decode("utf-8")
    found = set()
    in_cmd_block = False
    for line in lines.split("\n"):
        line = line.strip(" \t\n")
        if not in_cmd_block:
            if line.lower() == "commands:":
                in_cmd_block = True
            continue
        if len(line) == 0:
            break
        found.add(line.split(" ")[0])

    assert found == expected
