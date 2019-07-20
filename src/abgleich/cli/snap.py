# -*- coding: utf-8 -*-

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

@click.command(short_help = 'show dataset tree')
def snap():
	cols = ['NAME', 'USED', 'REFER', 'compressratio']
	col_align = ('left', 'right', 'right', 'decimal')
	size_cols = ['USED', 'REFER']
	datasets = get_tree()

	table = []
	for dataset in datasets:
		table.append([dataset[col] for col in cols])
		for snapshot in dataset['SNAPSHOTS']:
			table.append(['- ' + snapshot['NAME']] + [snapshot[col]for col in cols[1:]])
	for row in table:
		for col in [1, 2]:
			row[col] = humanize_size(int(row[col]), add_color = True)
		if not row[0].startswith('- '):
			row[0] = colorize(row[0], 'white')
		else:
			row[0] = colorize(row[0], 'grey')

	print(tabulate(
		table,
		headers = cols,
		tablefmt = 'github',
		colalign = col_align
		))
