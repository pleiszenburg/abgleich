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
	table = []
	for element in diff:
		element = ['' if item == False else item for item in element]
		element = ['X' if item == True else item for item in element]
		element = ['- ' + item[1:] if item.startswith('@') else item for item in element]
		table.append(element)
	print(tabulate(
		table,
		headers = ['NAME', 'LOCAL', 'REMOTE'],
		tablefmt = 'github'
		))
