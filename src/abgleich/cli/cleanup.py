# -*- coding: utf-8 -*-

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
	print(datasets[0])

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
