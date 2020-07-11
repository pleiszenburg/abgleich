# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

	src/abgleich/cli/cleanup.py: cleanup command entry point

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

from ..io import colorize, humanize_size
from ..zfs import (
	get_tree,
	get_cleanup_tasks,
	delete_snapshot,
	)

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ROUTINES
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@click.command(short_help = 'cleanup older snapshots')
@click.argument('configfile', type = click.File('r', encoding = 'utf-8'))
def cleanup(configfile):

	config = yaml.load(configfile.read(), Loader = CLoader)

	cols = ['NAME', 'DELETE SNAPSHOT']
	col_align = ('left', 'left')
	datasets = get_tree()
	cleanup_tasks = get_cleanup_tasks(
		datasets,
		config['prefix_local'],
		config['ignore'],
		config['keep_snapshots']
		)
	space_before = int(datasets[0]['AVAIL'])

	table = []
	for name, snapshot_name in cleanup_tasks:
		table.append([
			name,
			snapshot_name
			])

	print(tabulate(
		table,
		headers = cols,
		tablefmt = 'github',
		colalign = col_align
		))
	print('%s available' % humanize_size(space_before, add_color = True))

	click.confirm('Do you want to continue?', abort = True)

	for name, snapshot_name in cleanup_tasks:
		delete_snapshot(
			config['prefix_local'] + name,
			snapshot_name,
			# debug = True
			)

	space_after = int(get_tree()[0]['AVAIL'])
	print('%s available' % humanize_size(space_before, add_color = True))
	print('%s freed' % humanize_size(space_before - space_before, add_color = True))
