# -*- coding: utf-8 -*-

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# IMPORT
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

from ..cmd import (
	run_command,
	ssh_command,
	)

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ROUTINES
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def merge_snapshots_into_datasets(datasets, snapshots):

	for dataset in datasets:
		dataset['SNAPSHOTS'] = []
	datasets_dict = {dataset['NAME']: dataset for dataset in datasets}
	for snapshot in snapshots:
		dataset_name, snapshot['NAME'] = snapshot['NAME'].split('@')
		datasets_dict[dataset_name]['SNAPSHOTS'].append(snapshot)

def get_tree(host = None):

	cmd_list = ['zfs', 'list']
	cmd_list_snapshot = ['zfs', 'list', '-t', 'snapshot']

	if host is not None:
		cmd_list = ssh_command(host, cmd_list, compression = True)
		cmd_list_snapshot = ssh_command(host, cmd_list_snapshot, compression = True)

	datasets = parse_table(run_command(cmd_list))
	snapshots = parse_table(run_command(cmd_list_snapshot))
	merge_snapshots_into_datasets(datasets, snapshots)

	return datasets

def parse_table(raw):

	lines = raw.split('\n')
	table = [
		[item for item in line.split('  ') if len(item.strip()) != 0]
		for line in lines if len(line.strip()) != 0
		]
	head = table.pop(0)
	return [{k: v for k, v in zip(head, line)} for line in table]
