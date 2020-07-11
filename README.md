# ABGLEICH

## SYNOPSIS

Simple ZFS sync tool. Shows local and remote ZFS dataset trees / zpools. Creates meaningful snapshots only if datasets have actually been changed. Compares a local dataset tree to a remote, backup dataset tree. Pushes backups to remote. Cleanes up older snapshot on local system. Runs form the command line and produces nice, user-friendly, readable, colorized output.

## INSTALLATION

```bash
pip install -vU git+https://github.com/pleiszenburg/abgleich.git@master
```

Requires (C)Python 3.5 or later. Tested with ZoL 0.7 and 0.8.

## USAGE

### `abgleich tree config.yaml [source|target]`

Show zfs tree with snapshots, disk space and compression ratio. Append `source` or `target` (optional). `ssh` without password (public key) required.

### `abgleich snap config.yaml`

Determine which datasets have been changed since last snapshot. Generate snapshots where applicable. Superuser privileges required.

### `abgleich compare config.yaml`

Compare local machine with remote host. See what is missing where. `ssh` without password (public key) required. Superuser privileges required.

### `abgleich backup config.yaml`

Send (new) datasets and snapshots to remote host. `ssh` without password (public key) required. Superuser privileges required.

### `abgleich cleanup config.yaml`

Cleanup older local snapshots. Keep `keep_snapshots` number of snapshots. Superuser privileges required.

### `config.yaml`

Example configuration file:

```yaml
prefix_local: tank_ssd
prefix_remote: tank_hdd/BACKUP_SOMEMACHINE
host: bigdata
keep_snapshots: 2
ignore:
    - /ernst/CACHE
    - /ernst/CCACHE
```
