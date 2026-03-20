# Abgleich

> [!NOTE]
> As of version 0.2, this software is primarily written in Rust. Check branches `release_0.1` or `release_0.0` in case you looking for the original Python implementation.

`abgleich` is an opinionated [ZFS](https://en.wikipedia.org/wiki/ZFS) management and backup tool, to a certain extend inspired by workflows established by [distributed version control](https://en.wikipedia.org/wiki/Distributed_version_control) software like `git`. Think of snapshots as commits. No change, no snapshot, unless you say so explicitly. While branches are allowed, the downside is that classic merges and rebases are technically not feasible on ZFS. Nevertheless, `abgleich` can efficiently transfer ZFS datasets and snapshots from one zpool to another, regardless of the zpools' locations. Push and pull operation is therefore possible, but also transfers between two remote hosts.

## Installation

`abgleich` is written in Rust and can be statically linked against [musl](https://en.wikipedia.org/wiki/Musl), allowing self-contained portable binaries, trivial deployment and maximum compatibility. The primary target platforms are **Linux** and **FreeBSD** on x86_64. Both x86 (32 bit) and ARM support are theoretically trivial but currently untested territory - pull requests welcome. `abgleich` does not need to run on any target system, only the box where it gets invoked. Everything else is left to `ssh`, `sh`/`bash` and the operating system.

### Pre-Built Binaries

Pre-built binaries for Linux and FreeBSD can be found on the [releases page](https://github.com/pleiszenburg/abgleich/releases).

You can use the following command on Linux or FreeBSD to download the latest release. Simply replace `DEST` with the directory where you would like to put `abgleich`:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://abgleich.pleiszenburg.de/install.sh | bash -s -- --to DEST
```

For example, to install `abgleich` to `~/bin`:

```bash
# create ~/bin
mkdir -p ~/bin

# download and extract abgleich to ~/bin/abgleich
curl --proto '=https' --tlsv1.2 -sSf https://abgleich.pleiszenburg.de/install.sh | bash -s -- --to ~/bin

# add `~/bin` to the paths that your shell searches for executables
# this line should be added to your shells initialization file,
# e.g. `~/.bashrc` or `~/.zshrc`
export PATH="$PATH:$HOME/bin"

# abgleich should now be executable
abgleich --help
```

### Dependencies

Certain synchronization operations specifically require `bash`, `pv`, `nc` and `xz` to be present on certain hosts.

## Quick Start

Minimal typical setup: A workstation with a local ZFS pool `tank` whose datasets are snapshotted and then synced to a remote backup machine `nas` that has a pool called `backup`. SSH access to `nas` is assumed to work with public-key authentication, and the login user can run ZFS commands as `root` via passwordless `sudo`.

### Inspect pools

```bash
# list all zpools visible on localhost
abgleich ls

# show the dataset tree of a local pool
abgleich ls tank

# show a subsection of the dataset tree of a local pool
abgleich ls tank/some/data/set

# list zpools visible on the remote host
abgleich ls nas:

# show a dataset tree of the remote host
abgleich ls nas:tank
```

### Snapshot

```bash
abgleich snap tank
```

`abgleich` lists planned transactions and asks for confirmation before executing aforementioned transactions, i.e. changing anything. Think of `gparted`. Datasets that have not changed since the last snapshot are skipped by default. The current user is assumed to be allowed to create snapshots. If another user is allowed to create snapshots and passwordless `sudo` to said user for `zfs` is allowed:

```bash
abgleich snap otheruser%tank
```

### Sync to backup

```bash
abgleich sync tank nas:root%backup
```

`nas:root%backup` is the location of the target: `nas` is the SSH hostname, `root%` means ZFS commands are run as `root` via `sudo` on the remote side, and `backup` is the target pool. The first run performs a full initial transfer. Subsequent runs send only the snapshots added since the last sync.

### Free old snapshots from source

Once snapshots exist safely on the backup, the oldest ones can be removed from the source, `tank`, to reclaim space:

```bash
abgleich free tank nas:root%backup
```

By default, the two most recent snapshots shared with the backup are always kept on the source.

### Automation

The `-y` flag skips the confirmation prompt, which is useful for unattended scripts and cron jobs. For scripts, all commands can also generate JSON output using `-j`.

```bash
abgleich snap -yj tank
abgleich sync -yj tank nas:root%backup
abgleich free -yj tank nas:root%backup
```

### Configuration

Short aliases for locations and can be configured via an `abgleich.yaml` config file. Custom per-dataset ZFS properties allow fine-grained control, i.e. snapshot policy, overlap count and more.

## Concept: Locations

ZFS datasets are addressed through **locations**. Locations have three fragments:

1. An optional **route**, a sequence of hosts that `abgleich` can use to "hop" through using `ssh`, separated by forward slashes, `/`. If left empty or not present, `localhost` is assumed and `ssh` is not used. If a route is specified, it is terminated with a colon, `:`.
2. An optional **user** name used to gain required privileges for ZFS operations on the target system, the "final" host. If not present, the current user is assumed to have sufficient privileges. If a user is specified, it is terminated with a percent sign, `%`.
3. A **root** dataset , optionally followed by a single forward slash, `/`.

Example: `gateway/backupbox:backupuser%tank/some/dataset`.

`abgleich` would first ssh into `gateway` and from there into `backupbox`. It would then use `sudo -u backupuser [command]` to gain required privileges and perform `command`, likely against `tank/some/dataset`. Logins with `ssh` are assumed to work without passwords, i.e. with public keys instead. `ssh`'s configuration is left entirely to `ssh`, e.g. through the contents of `~/.ssh` and/or `/etc/ssh`. From a security point of view, it is assumed that the user allowed to perform ZFS operations is not necessarily the same user allowed to log in via `ssh`. However, it is assumed that the login user can use `sudo -u [username]` or simply `sudo` (for user `root`) without password for all relevant ZFS commands, e.g. `zfs` and `zpool`, among others.

Operations usually target a certain dataset and possibly its descendants. Similar to shell operations on directories, `abgleich` uses a tailing slash to indicate that only descendants are targeted but not the root dataset. Without the slash as in the above example, `tank/some/dataset` and its descendants are both targeted. With a tailing slash, i.e. `tank/some/dataset/`, the dataset `dataset` itself is excluded.

## Backwards Compatibility

If you are relying on `abgleich`, please notice that it uses **semantic versioning**. Breaking changes are indicated by increasing the second version number, the minor version. Going for example from ``0.0.x`` to ``0.1.y`` or going from ``0.1.x`` to ``0.2.y`` therefore indicates a breaking change.
