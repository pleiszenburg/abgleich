# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

	src/abgleich/cli/snap.py: snap command entry point

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

import click

from ..config import Config
from ..zfs.zpool import Zpool

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ROUTINES
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@click.command(short_help="create snapshots of changed datasets for backups")
@click.argument("configfile", type=click.File("r", encoding="utf-8"))
def snap(configfile):

    zpool = Zpool.from_config('source', config = Config.from_fd(configfile))

    # config = yaml.load(configfile.read(), Loader=CLoader)
	#
    # cols = ["NAME", "written", "FUTURE SNAPSHOT"]
    # col_align = ("left", "right")
    # datasets = get_tree()
    # snapshot_tasks = get_snapshot_tasks(
    #     datasets, config["prefix_local"], config["ignore"]
    # )
	#
    # table = []
    # for name, written, snapshot_name in snapshot_tasks:
    #     table.append([name, humanize_size(written, add_color=True), snapshot_name])
	#
    # print(tabulate(table, headers=cols, tablefmt="github", colalign=col_align))
	#
    # click.confirm("Do you want to continue?", abort=True)
	#
    # for name, _, snapshot_name in snapshot_tasks:
    #     create_snapshot(
    #         config["prefix_local"] + name,
    #         snapshot_name,
    #         # debug = True
    #     )
