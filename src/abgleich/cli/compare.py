# -*- coding: utf-8 -*-

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# IMPORT
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import click
from tabulate import tabulate

from ..zfs import (
	compare_trees,
	get_tree
	)

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ROUTINES
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@click.command(short_help = 'compare dataset trees')
@click.argument('host', type = str)
@click.argument('prefix_local', type = str)
@click.argument('prefix_remote', type = str)
def compare(host, prefix_local, prefix_remote):
	datasets_local = get_tree()
	datasets_remote = get_tree(host)
	diff = compare_trees(datasets_local, prefix_local, datasets_remote, prefix_remote)
	for item in diff:
		print(item)
	# table = []
	# for dataset in datasets:
	# 	table.append([dataset['NAME']])
	# 	for snapshot in dataset['SNAPSHOTS']:
	# 		table.append(['- ' + snapshot['NAME']])
	# print(tabulate(
	# 	table,
	# 	headers = ['NAME'],
	# 	tablefmt = 'github'
	# 	))
