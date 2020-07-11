# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

	src/abgleich/cli/tree.py: tree command entry point

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
from tabulate import tabulate

from ..io import colorize, humanize_size
from ..zfs import get_tree

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ROUTINES
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@click.command(short_help="show dataset tree")
@click.argument("host", default="localhost", type=str)
def tree(host):
    cols = ["NAME", "USED", "REFER", "compressratio"]
    col_align = ("left", "right", "right", "decimal")
    size_cols = ["USED", "REFER"]
    datasets = get_tree(host if host != "localhost" else None)
    table = []
    for dataset in datasets:
        table.append([dataset[col] for col in cols])
        for snapshot in dataset["SNAPSHOTS"]:
            table.append(
                ["- " + snapshot["NAME"]] + [snapshot[col] for col in cols[1:]]
            )
    for row in table:
        for col in [1, 2]:
            row[col] = humanize_size(int(row[col]), add_color=True)
        if not row[0].startswith("- "):
            row[0] = colorize(row[0], "white")
        else:
            row[0] = colorize(row[0], "grey")
    print(tabulate(table, headers=cols, tablefmt="github", colalign=col_align))
