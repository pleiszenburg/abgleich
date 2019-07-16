# -*- coding: utf-8 -*-

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# IMPORT
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import importlib
import os

import click

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ROUTINES
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def _add_commands(ctx):
	"""auto-detects sub-commands"""
	for cmd in (
		item[:-3] if item.lower().endswith('.py') else item[:]
		for item in os.listdir(os.path.dirname(__file__))
		if not item.startswith('_')
		):
		ctx.add_command(getattr(importlib.import_module(
			'abgleich.cli.%s' % cmd
			), cmd))

@click.group()
def cli():
	"""abgleich, btrfs and zfs sync tool"""

_add_commands(cli)
