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
	compare_trees,
	get_tree
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
	diff = compare_trees(
		datasets_local,
		config['prefix_local'],
		datasets_remote,
		config['prefix_remote']
		)
	table = []

	for element in diff:

		if element[0] in config['ignore']:
			continue
		if '@' in element[0]:
			if element[0].split('@')[0] in config['ignore']:
				continue
		if element[1] == True and element[2] == True:
			continue
		if element[1] == False and element[2] == True:
			continue

		element = ['' if item == False else item for item in element]
		element = ['X' if item == True else item for item in element]
		# element = ['- ' + item.split('@')[1] if '@' in item else item for item in element]
		if element[1:] == ['X', '']:
			element[1] = colorize(element[1], 'red')
		elif element[1:] == ['X', 'X']:
			element[1], element[2] = colorize(element[1], 'green'), colorize(element[2], 'green')
		elif element[1:] == ['', 'X']:
			element[2] = colorize(element[2], 'blue')
		if '@' not in element[0]:
			element[0] = colorize(element[0], 'white')
		else:
			element[0] = colorize(element[0], 'grey')
		table.append(element)

	print(tabulate(
		table,
		headers = ['NAME', 'LOCAL', 'REMOTE'],
		tablefmt = 'github'
		))
