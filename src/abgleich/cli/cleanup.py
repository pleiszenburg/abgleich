# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/cli/cleanup.py: cleanup command entry point

    Copyright (C) 2019-2022 Sebastian M. Ernst <ernst@pleiszenburg.de>

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

import time
import sys

import click

from ..core.config import Config
from ..core.i18n import t
from ..core.io import humanize_size
from ..core.lib import is_host_up
from ..core.zpool import Zpool

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ROUTINES
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@click.command(short_help="cleanup older snapshots")
@click.argument("configfile", type=click.File("r", encoding="utf-8"))
@click.argument("side", default="source", type=str)
def cleanup(configfile, side):

    config = Config.from_fd(configfile)

    assert side in ("source", "target")

    cleanup_side = side
    control_side = "target" if cleanup_side == "source" else "source"

    if cleanup_side == "target":
        click.confirm(
            t(
                "DANGER ZONE: You are about to clean the TARGET. Do you want to continue?"
            ),
            abort=True,
        )
        if config["keep_backlog"].value == True:
            print(t("nothing to do"))
            return

    for side in (cleanup_side, control_side):
        if not is_host_up(side, config):
            print(f'{t("host is not up"):s}: {side:s}')
            sys.exit(1)

    cleanup_zpool = Zpool.from_config(cleanup_side, config=config)
    control_zpool = Zpool.from_config(control_side, config=config)
    available_before = Zpool.available(cleanup_side, config=config)

    transactions = cleanup_zpool.get_cleanup_transactions(control_zpool)

    if len(transactions) == 0:
        print(t("nothing to do"))
        return
    transactions.print_table()

    click.confirm(t("Do you want to continue?"), abort=True)

    transactions.run()

    WAIT = 10
    print(f"waiting {WAIT:d} seconds ...")
    time.sleep(WAIT)
    available_after = Zpool.available(cleanup_side, config=config)
    print(
        (
            f"{humanize_size(available_after, add_color = True):s} available, "
            f"{humanize_size(available_after - available_before, add_color = True):s} freed"
        )
    )
