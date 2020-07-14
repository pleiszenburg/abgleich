# ABGLEICH

## SYNOPSIS

`abgleich` is a simple ZFS sync tool. It shows source and target ZFS zpool, dataset and snapshot trees. It creates meaningful snapshots only if datasets have actually been changed. It compares a source zpool tree to a target, backup zpool tree. It pushes backups from a source to a target. It cleanes up older snapshots on the source side if they are present on the target side. It runs on the command line and produces nice, user-friendly, human-readable, colorized output.

## INSTALLATION

```bash
pip install -vU git+https://github.com/pleiszenburg/abgleich.git@master
```

Requires (C)Python 3.6 or later. Tested with [OpenZFS](https://en.wikipedia.org/wiki/OpenZFS) 0.8.x on Linux.

## USAGE

All potentially changing or destructive actions are listed in detail before the user is asked to confirm them. None of the commands listed below create, change or destroy a zpool, dataset or snapshot on their own without the user's explicit consent.

### `abgleich tree config.yaml [source|target]`

Show zfs tree with snapshots, disk space and compression ratio. Append `source` or `target` (optional). `ssh` without password (public key) required if source and/or target is not equivalent to localhost.

### `abgleich snap config.yaml`

Determine which datasets have been changed since last snapshot. Generate snapshots where applicable. `ssh` without password (public key) required if source and/or target is not equivalent to localhost. Superuser privileges required.

### `abgleich compare config.yaml`

Compare local machine with remote host. See what is missing where. `ssh` without password (public key) required if source and/or target is not equivalent to localhost.

### `abgleich backup config.yaml`

Send (new) datasets and snapshots to target host. `ssh` without password (public key) required if source and/or target is not equivalent to localhost. Superuser privileges required.

### `abgleich cleanup config.yaml`

Cleanup older local snapshots. Keep `keep_snapshots` number of snapshots. `ssh` without password (public key) required if source and/or target is not equivalent to localhost. Superuser privileges required.

### Speed

For (recommended) safety, `abgleich` runs fully statically typed by default, i.e. insanely slow. For must higher speed, the checks can be deactivated by setting the `PYTHONOPTIMIZE` environment variable to `1` or `2`, e.g. `PYTHONOPTIMIZE=1 abgleich tree config.yaml`.

### `config.yaml`

Example configuration file:

```yaml
source:
    zpool: tank_ssd
    prefix:
    host: localhost
    user:
target:
    zpool: tank_hdd
    prefix: BACKUP_SOMEMACHINE
    host: bigdata
    user: root
keep_snapshots: 2
suffix: _backup
digits: 2
ignore:
    - user/CACHE
    - user/CCACHE
ssh:
    compression: no
    cipher: aes256-gcm@openssh.com
```

The prefix can be empty on either side. If a `host` is `localhost`, the `user` field can be left empty. Both source and target can be remote hosts at the same time or localhost at the same time. `keep_snapshots` is an integer and must greater or equal to `1`. `suffix` describes the name suffix for new snapshots. `digits` specifies how many digits are used for a decimal number describing the n-th snapshot per dataset per day as part of the name of new snapshots. `ignore` lists stuff underneath the `prefix` which will be ignored by this tool, i.e. no snapshots, backups or cleanups. `ssh` allows to fine-tune the speed of backups. In fast local networks, it is best to set `compression` to `no` because the compression is usually slowing down the transfer. However, for low-bandwidth transmissions, it makes sense to set it to `yes`. For significantly better speed in fast local networks, make sure that both the source and the target system support a common cipher, which is accelerated by [AES-NI](https://en.wikipedia.org/wiki/AES_instruction_set) on both ends.
