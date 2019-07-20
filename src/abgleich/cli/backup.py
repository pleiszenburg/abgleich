# -*- coding: utf-8 -*-

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
