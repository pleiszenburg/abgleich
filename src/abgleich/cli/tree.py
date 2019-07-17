# -*- coding: utf-8 -*-

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# IMPORT
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import click
from ..zfs import get_tree

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ROUTINES
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@click.command(short_help = 'show dataset tree')
@click.argument('host', default = 'localhost', type = str)
def tree(host):
	datasets = get_tree(host if host != 'localhost' else None)
	for dataset in datasets:
		print(dataset['NAME'])
		for snapshot in dataset['SNAPSHOTS']:
			print('\t' + snapshot['NAME'])
