# -*- coding: utf-8 -*-

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# IMPORT
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import click
from tabulate import tabulate

from ..io import humanize_size
from ..zfs import get_tree

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ROUTINES
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@click.command(short_help = 'show dataset tree')
@click.argument('host', default = 'localhost', type = str)
def tree(host):
	cols = ['NAME', 'USED', 'REFER', 'compressratio']
	col_align = ('left', 'right', 'right', 'decimal')
	size_cols = ['USED', 'REFER']
	datasets = get_tree(host if host != 'localhost' else None)
	table = []
	for dataset in datasets:
		table.append([
			dataset[col] if col not in size_cols else humanize_size(int(dataset[col]))
			for col in cols
			])
		for snapshot in dataset['SNAPSHOTS']:
			table.append(['- ' + snapshot['NAME']] + [
				snapshot[col] if col not in size_cols else humanize_size(int(snapshot[col]))
				for col in cols[1:]
				])
	print(tabulate(
		table,
		headers = cols,
		tablefmt = 'github',
		colalign = col_align
		))
