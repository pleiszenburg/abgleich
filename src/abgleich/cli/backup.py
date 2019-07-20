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
	ops = get_backup_ops(
		datasets_local,
		config['prefix_local'],
		datasets_remote,
		config['prefix_remote'],
		config['ignore']
		)

	print(tabulate(
		ops,
		headers = ['OP', 'SOURCE', 'DESTINATION'],
		tablefmt = 'github'
		))
