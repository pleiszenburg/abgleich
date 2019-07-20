# -*- coding: utf-8 -*-

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# IMPORT
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import datetime

import click
from tabulate import tabulate
import yaml
from yaml import CLoader

from ..io import colorize, humanize_size
from ..zfs import (
	create_snapshot,
	get_tree,
	get_snapshot_tasks,
	)

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ROUTINES
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@click.command(short_help = 'create snapshots of changed datasets for backups')
@click.argument('configfile', type = click.File('r', encoding = 'utf-8'))
def snap(configfile):

	config = yaml.load(configfile.read(), Loader = CLoader)

	cols = ['NAME', 'written']
	col_align = ('left', 'right')
	datasets = get_tree()
	snapshot_tasks = get_snapshot_tasks(
		datasets,
		config['prefix_local'],
		config['ignore']
		)

	table = []
	for name, written in snapshot_tasks:
		table.append([
			name,
			humanize_size(written, add_color = True)
			])

	print(tabulate(
		table,
		headers = cols,
		tablefmt = 'github',
		colalign = col_align
		))

	click.confirm('Do you want to continue?', abort = True)

	date = datetime.datetime.now().strftime('%Y%m%d')

	for name, _ in snapshot_tasks:
		create_snapshot(
			config['prefix_local'] + name,
			date + config['suffix_snapshot'],
			debug = True
			)
