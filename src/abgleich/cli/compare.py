# -*- coding: utf-8 -*-

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# IMPORT
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import click
from tabulate import tabulate

from ..zfs import get_tree

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ROUTINES
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@click.command(short_help = 'compare dataset trees')
@click.argument('host', default = 'localhost', type = str)
def compare(host):
	datasets = get_tree(host if host != 'localhost' else None)
	table = []
	for dataset in datasets:
		table.append([dataset['NAME']])
		for snapshot in dataset['SNAPSHOTS']:
			table.append(['- ' + snapshot['NAME']])
	print(tabulate(
		table,
		headers = ['NAME'],
		tablefmt = 'github'
		))
