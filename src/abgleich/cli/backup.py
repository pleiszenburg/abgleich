# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

	src/abgleich/cli/backup.py: backup command entry point

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
import yaml
from yaml import CLoader

from ..io import colorize
from ..zfs import (
	get_backup_ops,
	get_tree,
	push_snapshot,
	push_snapshot_incremental,
	)

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ROUTINES
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@click.command(short_help = 'backup a dataset tree into another')
@click.argument('configfile', type = click.File('r', encoding = 'utf-8'))
def backup(configfile):

	config = yaml.load(configfile.read(), Loader = CLoader)

	datasets_local = get_tree()
	datasets_remote = get_tree(config['host'])
	ops = get_backup_ops(
		datasets_local,
		config['prefix_local'],
		datasets_remote,
		config['prefix_remote'],
		config['ignore']
		)

	table = []
	for op in ops:
		row = op.copy()
		row[0] = colorize(row[0], 'green' if 'incremental' in row[0] else 'blue')
		table.append(row)

	print(tabulate(
		table,
		headers = ['OP', 'PARAM'],
		tablefmt = 'github'
		))

	click.confirm('Do you want to continue?', abort = True)

	for op, param in ops:
		if op == 'push_snapshot':
			push_snapshot(
				config['host'],
				config['prefix_local'] + param[0],
				param[1],
				config['prefix_remote'] + param[0],
				# debug = True
				)
		elif op == 'push_snapshot_incremental':
			push_snapshot_incremental(
				config['host'],
				config['prefix_local'] + param[0],
				param[1], param[2],
				config['prefix_remote'] + param[0],
				# debug = True
				)
		else:
			raise ValueError('unknown operation')
