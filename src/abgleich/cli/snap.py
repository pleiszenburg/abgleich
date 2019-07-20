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
	snapshot_tasks = get_snapshot_tasks(datasets)

	table = []
	for name, written in snapshot_tasks:
		table.append([
			name[len(config['prefix_local']):],
			humanize_size(written, add_color = True)
			])

	print(tabulate(
		table,
		headers = cols,
		tablefmt = 'github',
		colalign = col_align
		))
