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
	subdict_a = {
		'/' + dataset['NAME'][len(prefix_a):]: dataset
		for dataset in tree_a
		if dataset['NAME'].startswith(prefix_a) # or dataset['NAME'] == prefix_a[:-1]
		}
	subdict_b = {
		'/' + dataset['NAME'][len(prefix_b):]: dataset
		for dataset in tree_b
		if dataset['NAME'].startswith(prefix_b) # or dataset['NAME'] == prefix_b[:-1]
		}
	tree_names = list(sorted(subdict_a.keys() | subdict_b.keys()))
	res = list()
	for name in tree_names:
		res.append([name, name in subdict_a.keys(), name in subdict_b.keys()])
		res.extend(__merge_snapshots__(
			name,
			subdict_a[name]['SNAPSHOTS'] if name in subdict_a else list(),
			subdict_b[name]['SNAPSHOTS'] if name in subdict_b else list()
			))
	return res

def __merge_snapshots__(dataset_name, snap_a, snap_b):
	if len(snap_a) == 0 and len(snap_b) == 0:
		return list()
	names_a = [snapshot['NAME'] for snapshot in snap_a]
	names_b = [snapshot['NAME'] for snapshot in snap_b]
	if len(names_a) == 0 and len(names_b) > 0:
		return [[dataset_name + '@' + name, False, True] for name in names_b]
	if len(names_b) == 0 and len(names_a) > 0:
		return [[dataset_name + '@' + name, True, False] for name in names_a]
	creations_a = {snapshot['creation']: snapshot for snapshot in snap_a}
	creations_b = {snapshot['creation']: snapshot for snapshot in snap_b}
	creations = list(sorted(creations_a.keys() | creations_b.keys()))
	ret = list()
	for creation in creations:
		in_a = creation in creations_a.keys()
		in_b = creation in creations_b.keys()
		if in_a:
			name = creations_a[creation]['NAME']
		elif in_b:
			name = creations_b[creation]['NAME']
		else:
			raise ValueError('this should not happen')
		if in_a and in_b:
			if creations_a[creation]['NAME'] != creations_b[creation]['NAME']:
				raise ValueError('snapshot name mismatch for equal creation times')
		ret.append([dataset_name + '@' + name, in_a, in_b])
	return ret

def get_backup_ops(tree_a, prefix_a, tree_b, prefix_b, ignore):
	assert not prefix_a.endswith('/')
	assert not prefix_b.endswith('/')
	prefix_a += '/'
	prefix_b += '/'
	subdict_a = {
		'/' + dataset['NAME'][len(prefix_a):]: dataset
		for dataset in tree_a
		if dataset['NAME'].startswith(prefix_a)
		}
	subdict_b = {
		'/' + dataset['NAME'][len(prefix_b):]: dataset
		for dataset in tree_b
		if dataset['NAME'].startswith(prefix_b)
		}
	tree_names = list(sorted(subdict_a.keys() | subdict_b.keys()))
	res = list()
	for name in tree_names:
		if name in ignore:
			continue
		dataset_in_a = name in subdict_a.keys()
		dataset_in_b = name in subdict_b.keys()
		if not dataset_in_a and dataset_in_b:
			raise ValueError('no source dataset "%s" - only remote' % name)
		if dataset_in_a and not dataset_in_b and len(subdict_a[name]['SNAPSHOTS']) == 0:
			raise ValueError('no snapshots in dataset "%s" - can not send' % name)
		if dataset_in_a and not dataset_in_b:
			res.append([
				'push_snapshot',
				(name, subdict_a[name]['SNAPSHOTS'][0]['NAME'])
				])
			for snapshot_1, snapshot_2 in zip(
				subdict_a[name]['SNAPSHOTS'][:-1],
				subdict_a[name]['SNAPSHOTS'][1:]
				):
				res.append([
					'push_snapshot_incremental',
					(name, snapshot_1['NAME'], snapshot_2['NAME'])
					])
			continue
		last_remote_shapshot = subdict_b[name]['SNAPSHOTS'][-1]['NAME']
		source_index = None
		for index, source_snapshot in enumerate(subdict_a[name]['SNAPSHOTS']):
			if source_snapshot['NAME'] == last_remote_shapshot:
				source_index = index
				break
		if source_index is None:
			raise ValueError('no common snapshots in dataset "%s" - can not send incremental' % name)
		for snapshot_1, snapshot_2 in zip(
			subdict_a[name]['SNAPSHOTS'][source_index:-1],
			subdict_a[name]['SNAPSHOTS'][(source_index + 1):]
			):
			res.append([
				'push_snapshot_incremental',
				(name, snapshot_1['NAME'], snapshot_2['NAME'])
				])

	return res

def get_snapshot_tasks(tree):

	res = list()

	for dataset in tree:
		if dataset['MOUNTPOINT'] == 'none':
			continue
		if len(dataset['SNAPSHOTS']) == 0:
			res.append([dataset['NAME'], int(dataset['written'])])
			continue
		if int(dataset['written']) > (1024 ** 2):
			res.append([dataset['NAME'], int(dataset['written'])])
			continue
		diff_out = run_command([
			'zfs', 'diff', dataset['NAME'] + '@' + dataset['SNAPSHOTS'][-1]['NAME']
			])
		if len(diff_out.strip(' \t\n')) > 0:
			res.append([dataset['NAME'], int(dataset['written'])])

	return res

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
