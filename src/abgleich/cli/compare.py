# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

	src/abgleich/cli/compare.py: compare command entry point

	Copyright (C) 2019-2020 Sebastian M. Ernst <ernst@pleiszenburg.de>

<LICENSE_BLOCK>
The contents of this file are subject to the GNU Lesser General Public License
Version 2.1 ("LGPL" or "License"). You may not use this file except in
compliance with the License. You may obtain a copy of the License at
https://www.gnu.org/licenses/old-licenses/lgpl-2.1.txt
https://github.com/pleiszenburg/abgleich/blob/master/LICENSE

Software distributed under the License is distributed on an "AS IS" basis,
WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License for the
specific language governing rights and limitations under the License.
</LICENSE_BLOCK>

"""


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

@click.command(short_help = 'compare dataset trees')
@click.argument('configfile', type = click.File('r', encoding = 'utf-8'))
def compare(configfile):
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
		element = ['' if item == False else item for item in element]
		element = ['X' if item == True else item for item in element]
		element = ['- ' + item.split('@')[1] if '@' in item else item for item in element]
		if element[1:] == ['X', '']:
			element[1] = colorize(element[1], 'red')
		elif element[1:] == ['X', 'X']:
			element[1], element[2] = colorize(element[1], 'green'), colorize(element[2], 'green')
		elif element[1:] == ['', 'X']:
			element[2] = colorize(element[2], 'blue')
		if not element[0].startswith('- '):
			element[0] = colorize(element[0], 'white')
		else:
			element[0] = colorize(element[0], 'grey')
		table.append(element)
	print(tabulate(
		table,
		headers = ['NAME', 'LOCAL', 'REMOTE'],
		tablefmt = 'github'
		))
