# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/cli/_main_.py: CLI auto-detection

    Copyright (C) 2019-2020 Sebastian M. Ernst <ernst@pleiszenburg.de>

<LICENSE_BLOCK>
The contents of this file are subject to the GNU Lesser General Public License
Version 2.1 ("LGPL" or "License"). You may not use this file except in
compliance with the License. You may obtain a copy of the License at
https://www.gnu.org/licenses/old-licenses/lgpl-2.1.txt
https://github.com/pleiszenburg/abgleich/blob/master/LICENSE

Software distributed under the License is distributed on an "AS IS" basis,
WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License for the
specific language governing rights and limitations under the License.
</LICENSE_BLOCK>

"""


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# IMPORT
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import importlib
import os
import sys

import click

from .. import __version__

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ROUTINES
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


def _add_commands(ctx):
    """auto-detects sub-commands"""
    for cmd in (
        item[:-3] if item.lower().endswith(".py") else item[:]
        for item in os.listdir(os.path.dirname(__file__))
        if not item.startswith("_")
    ):
        try:
            ctx.add_command(
                getattr(importlib.import_module("abgleich.cli.%s" % cmd), cmd)
            )
        except ModuleNotFoundError:  # likely no gui support
            continue


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True)
def cli(version):
    """abgleich, zfs sync tool"""

    if not version:
        return

    print(__version__)
    sys.exit()


_add_commands(cli)
