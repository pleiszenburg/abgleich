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

def get_tree(host = None):

	cmd_list = ['zfs', 'list', '-H', '-p']
	cmd_list_snapshot = ['zfs', 'list', '-t', 'snapshot', '-H', '-p']

	if host is not None:
		cmd_list = ssh_command(host, cmd_list, compression = True)
		cmd_list_snapshot = ssh_command(host, cmd_list_snapshot, compression = True)

	datasets = parse_table(run_command(cmd_list))
	snapshots = parse_table(run_command(cmd_list_snapshot))
	merge_snapshots_into_datasets(datasets, snapshots)

	return datasets

def merge_snapshots_into_datasets(datasets, snapshots):

	for dataset in datasets:
		dataset['SNAPSHOTS'] = []
	datasets_dict = {dataset['NAME']: dataset for dataset in datasets}
	for snapshot in snapshots:
		dataset_name, snapshot['NAME'] = snapshot['NAME'].split('@')
		datasets_dict[dataset_name]['SNAPSHOTS'].append(snapshot)

def parse_table(raw):

	head = ['NAME', 'USED', 'AVAIL', 'REFER', 'MOUNTPOINT']
	table = [item.split('\t') for item in raw.split('\n') if len(item.strip()) > 0]
	return [{k: v for k, v in zip(head, line)} for line in table]

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ROUTINES: SEND & RECEIVE
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def receive_snapshot(host, src, src_firstsnapshot, dest):
	print('RECEIVING FIRST %s@%s to %s ...' % (src, src_firstsnapshot, dest))
	cmd1 = ssh_command(
		host,
		['zfs', 'send', '-c', '%s@%s' % (src, src_firstsnapshot)],
		compression = False
		)
	cmd2 = ['zfs', 'receive', dest]
	run_chain_command(cmd1, cmd2)
	print('... DONE.')

def receive_snapshot_incremental(host, src, src_a, src_b, dest):
	print('RECEIVING FOLLOW-UP %s@[%s - %s] to %s ...' % (src, src_a, src_b, dest))
	cmd1 = ssh_command(
		host,
		['zfs', 'send', '-c', '-i', '%s@%s' % (src, src_a), '%s@%s' % (src, src_b)],
		compression = False
		)
	cmd2 = ['zfs', 'receive', dest]
	run_chain_command(cmd1, cmd2)
	print('... DONE.')

def receive_new(host, dataset_src, dest):
	src = dataset_src['NAME']
	src_firstsnapshot = dataset_src['SNAPSHOTS'][0]['NAME']
	src_snapshotpairs = [
		(a['NAME'], b['NAME'])
		for a, b in zip(dataset_src['SNAPSHOTS'][:-1], dataset_src['SNAPSHOTS'][1:])
		]
	receive_snapshot(host, src, src_firstsnapshot, dest)
	for src_a, src_b in src_snapshotpairs:
		receive_snapshot_incremental(host, src, src_a, src_b, dest)

def send_snapshot(host, src, src_firstsnapshot, dest):
	print('SENDING FIRST %s@%s to %s ...' % (src, src_firstsnapshot, dest))
	cmd1 = ['zfs', 'send', '-c', '%s@%s' % (src, src_firstsnapshot)]
	cmd2 = ssh_command(
		host,
		['zfs', 'receive', dest],
		compression = False
		)
	run_chain_command(cmd1, cmd2)
	print('... DONE.')

def send_snapshot_incremental(host, src, src_a, src_b, dest):
	print('SENDING FOLLOW-UP %s@[%s - %s] to %s ...' % (src, src_a, src_b, dest))
	cmd1 = [
		'zfs', 'send', '-c',
		'-i', '%s@%s' % (src, src_a), '%s@%s' % (src, src_b)
		]
	cmd2 = ssh_command(
		host,
		['zfs', 'receive', dest],
		compression = False
		)
	run_chain_command(cmd1, cmd2)
	print('... DONE.')

def send_new(host, dataset_src, dest):
	src = dataset_src['NAME']
	src_firstsnapshot = dataset_src['SNAPSHOTS'][0]['NAME']
	src_snapshotpairs = [
		(a['NAME'], b['NAME']) for a, b in zip(dataset_src['SNAPSHOTS'][:-1], dataset_src['SNAPSHOTS'][1:])
		]
	send_snapshot(host, src, src_firstsnapshot, dest)
	for src_a, src_b in src_snapshotpairs:
		send_snapshot_incremental(host, src, src_a, src_b, dest)
