# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/cli/backup.py: backup command entry point

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

import click
import sys

from ..core.config import Config
from ..core.i18n import t
from ..core.lib import is_host_up
from ..core.zpool import Zpool

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ROUTINES
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@click.command(short_help="backup a dataset tree into another")
@click.argument("configfile", type=click.File("r", encoding="utf-8"))
def backup(configfile):

    config = Config.from_fd(configfile)

    for side in ("source", "target"):
        if not is_host_up(side, config):
            print(f'{t("host is not up"):s}: {side:s}')
            sys.exit(1)

    source_zpool = Zpool.from_config("source", config=config)
    target_zpool = Zpool.from_config("target", config=config)

    transactions = source_zpool.get_backup_transactions(target_zpool)

    if len(transactions) == 0:
        print(t("nothing to do"))
        return
    transactions.print_table()

    click.confirm(t("Do you want to continue?"), abort=True)

    transactions.run()
