# ABGLEICH

btrfs and zfs sync tool

## `abgleich tree [hostname]`

Show zfs tree with snapshots, disk space and compression ratio. Append `hostname` (optional) for remote tree. Ssh without password (public key) required.

# `abgleich snap config.yaml`

Determine which datasets have been changed since last snapshot. Generate snapshots where applicable. Superuser privileges required.

# `abgleich compare config.yaml`

Compare local machine with remote host. See what is missing where. Ssh without password (public key) required. Superuser privileges required.

# `abgleich backup config.yaml`

Send (new) datasets and snapshots to remote host. Ssh without password (public key) required. Superuser privileges required.

# `config.yaml`

Example configuration file:

```yaml
prefix_local: tank_ssd
prefix_remote: tank_hdd/BACKUP_SOMEMACHINE
host: bigdata
ignore:
    - /ernst/CACHE
    - /ernst/CCACHE
```
