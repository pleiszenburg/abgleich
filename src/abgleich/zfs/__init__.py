# -*- coding: utf-8 -*-

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# IMPORT
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

from ..cmd import (
	run_chain_command,
	run_command,
	ssh_command,
	)

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ROUTINES
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def compare_trees(tree_a, prefix_a, tree_b, prefix_b):
	assert not prefix_a.endswith('/')
	assert not prefix_b.endswith('/')
	prefix_a += '/'
	prefix_b += '/'
	subtree_a = [
		dataset for dataset in tree_a
		if dataset['NAME'].startswith(prefix_a) and len(dataset['NAME']) > len(prefix_a)
		]
	subtree_b = [
		dataset for dataset in tree_b
		if dataset['NAME'].startswith(prefix_b) and len(dataset['NAME']) > len(prefix_b)
		]
	subdict_a = {dataset['NAME'][len(prefix_a):]: dataset for dataset in subtree_a}
	subdict_b = {dataset['NAME'][len(prefix_b):]: dataset for dataset in subtree_b}
	tree_names = list(sorted(subdict_a.keys() | subdict_b.keys()))
	res = list()
	for name in tree_names:
		res.append([name, name in subdict_a.keys(), name in subdict_b.keys()])
		res.extend(__merge_snapshots__(
			subdict_a[name]['SNAPSHOTS'] if name in subdict_a else list(),
			subdict_b[name]['SNAPSHOTS'] if name in subdict_b else list()
			))
	return res

def __merge_snapshots__(snap_a, snap_b):
	if len(snap_a) == 0 and len(snap_b) == 0:
		return list()
	names_a = [snapshot['NAME'] for snapshot in snap_a]
	names_b = [snapshot['NAME'] for snapshot in snap_b]
	if len(names_a) == 0 and len(names_b) > 0:
		return [['@' + name, False, True] for name in names_b]
	if len(names_b) == 0 and len(names_a) > 0:
		return [['@' + name, True, False] for name in names_a]
	creations_a = {snapshot['creation']: snapshot for snapshot in snap_a}
	creations_b = {snapshot['creation']: snapshot for snapshot in snap_b}
	creations = list(sorted(creations_a.keys() | creations_b.keys()))
	ret = list()
	for creation in creations:
		if creation in creations_a.keys():
			name = creations_a[creation]['NAME']
		else:
			name = creations_b[creation]['NAME']
		if creation in creations_a.keys() and creation in creations_b.keys():
			assert creations_a[creation]['NAME'] == creations_b[creation]['NAME']
		ret.append([
			'@' + name,
			creation in creations_a.keys(),
			creation in creations_b.keys()
			])
	return ret

def get_tree(host = None):

	cmd_list = ['zfs', 'list', '-H', '-p']
	cmd_list_snapshot = ['zfs', 'list', '-t', 'snapshot', '-H', '-p']
	cmd_list_property = ['zfs', 'get', 'all', '-H', '-p']

	if host is not None:
		cmd_list = ssh_command(host, cmd_list, compression = True)
		cmd_list_snapshot = ssh_command(host, cmd_list_snapshot, compression = True)
		cmd_list_property = ssh_command(host, cmd_list_property, compression = True)

	datasets = parse_table(
		run_command(cmd_list),
		['NAME', 'USED', 'AVAIL', 'REFER', 'MOUNTPOINT']
		)
	snapshots = parse_table(
		run_command(cmd_list_snapshot),
		['NAME', 'USED', 'AVAIL', 'REFER', 'MOUNTPOINT']
		)
	properties = parse_table(
		run_command(cmd_list_property),
		['NAME', 'PROPERTY', 'VALUE', 'SOURCE']
		)
	merge_properties(datasets, snapshots, properties)
	merge_snapshots_into_datasets(datasets, snapshots)

	return datasets

def merge_properties(datasets, snapshots, properties):

	elements = {dataset['NAME']: dataset for dataset in datasets}
	elements.update({snapshot['NAME']: snapshot for snapshot in snapshots})
	for property in properties:
		elements[property['NAME']][property['PROPERTY']] = property['VALUE']

def merge_snapshots_into_datasets(datasets, snapshots):

	for dataset in datasets:
		dataset['SNAPSHOTS'] = []
	datasets_dict = {dataset['NAME']: dataset for dataset in datasets}
	for snapshot in snapshots:
		dataset_name, snapshot['NAME'] = snapshot['NAME'].split('@')
		datasets_dict[dataset_name]['SNAPSHOTS'].append(snapshot)

def parse_table(raw, head):

	table = [item.split('\t') for item in raw.split('\n') if len(item.strip()) > 0]
	return [{k: v for k, v in zip(head, line)} for line in table]

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ROUTINES: SEND & RECEIVE
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def pull_snapshot(host, src, src_firstsnapshot, dest, debug = False):
	print('PULLING FIRST %s@%s to %s ...' % (src, src_firstsnapshot, dest))
	cmd1 = ssh_command(
		host,
		['zfs', 'send', '-c', '%s@%s' % (src, src_firstsnapshot)],
		compression = False
		)
	cmd2 = ['zfs', 'receive', dest]
	run_chain_command(cmd1, cmd2, debug = debug)
	print('... PULLING FIRST DONE.')

def pull_snapshot_incremental(host, src, src_a, src_b, dest, debug = False):
	print('PULLING FOLLOW-UP %s@[%s - %s] to %s ...' % (src, src_a, src_b, dest))
	cmd1 = ssh_command(
		host,
		['zfs', 'send', '-c', '-i', '%s@%s' % (src, src_a), '%s@%s' % (src, src_b)],
		compression = False
		)
	cmd2 = ['zfs', 'receive', dest]
	run_chain_command(cmd1, cmd2, debug = debug)
	print('... PULLING FOLLOW-UP DONE.')

def pull_new(host, dataset_src, dest, debug = False):
	print('PULLING NEW %s to %s ...' % (dataset_src['NAME'], dest))
	src = dataset_src['NAME']
	src_firstsnapshot = dataset_src['SNAPSHOTS'][0]['NAME']
	src_snapshotpairs = [
		(a['NAME'], b['NAME'])
		for a, b in zip(dataset_src['SNAPSHOTS'][:-1], dataset_src['SNAPSHOTS'][1:])
		]
	pull_snapshot(host, src, src_firstsnapshot, dest, debug = debug)
	for src_a, src_b in src_snapshotpairs:
		pull_snapshot_incremental(host, src, src_a, src_b, dest, debug = debug)
	print('... PULLING NEW DONE.')

def push_snapshot(host, src, src_firstsnapshot, dest, debug = False):
	print('PUSHING FIRST %s@%s to %s ...' % (src, src_firstsnapshot, dest))
	cmd1 = ['zfs', 'send', '-c', '%s@%s' % (src, src_firstsnapshot)]
	cmd2 = ssh_command(
		host,
		['zfs', 'receive', dest],
		compression = False
		)
	run_chain_command(cmd1, cmd2, debug = debug)
	print('... PUSHING FIRST DONE.')

def push_snapshot_incremental(host, src, src_a, src_b, dest, debug = False):
	print('PUSHING FOLLOW-UP %s@[%s - %s] to %s ...' % (src, src_a, src_b, dest))
	cmd1 = [
		'zfs', 'send', '-c',
		'-i', '%s@%s' % (src, src_a), '%s@%s' % (src, src_b)
		]
	cmd2 = ssh_command(
		host,
		['zfs', 'receive', dest],
		compression = False
		)
	run_chain_command(cmd1, cmd2, debug = debug)
	print('... PUSHING FOLLOW-UP DONE.')

def push_new(host, dataset_src, dest, debug = False):
	print('PUSHING NEW %s to %s ...' % (dataset_src['NAME'], dest))
	src = dataset_src['NAME']
	src_firstsnapshot = dataset_src['SNAPSHOTS'][0]['NAME']
	src_snapshotpairs = [
		(a['NAME'], b['NAME'])
		for a, b in zip(dataset_src['SNAPSHOTS'][:-1], dataset_src['SNAPSHOTS'][1:])
		]
	push_snapshot(host, src, src_firstsnapshot, dest, debug = debug)
	for src_a, src_b in src_snapshotpairs:
		push_snapshot_incremental(host, src, src_a, src_b, dest, debug = debug)
	print('... PUSHING NEW DONE.')
