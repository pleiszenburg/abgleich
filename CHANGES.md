# Changes

## Roadmap

- Sub-command for borrowing / lending a dataset temporarily to another zpool/machine while freezing it on the source
- Sub-command for moving a dataset and its backup to other machines
- Sub-command similar to `git branch` which creates a new dataset from a snapshot and optionally detached it
- Sub-command which (very poorly) mimics `git merge --squash`, possibly relying on `rsync`
- Resuming interrupted sending transactions, see [receive_resume_token](https://openzfs.github.io/openzfs-docs/man/master/8/zfs-receive.8.html#receive_resume_token)
- Some kind of light-weight native GUI, i.e. no Web or Electron application
- Translations / internationalization
- Python API around the Rust core crate for advanced scripting usage or integration into third-party web applications

## 0.2.0 (2026-XX-XX)

**CAUTION**: Deployment, CLI and configuration changed, **BREAKING BACKWARDS COMPATIBILITY** for all use-cases!

Complete Rust-rewrite, resulting in a fully statically linked, portable binary. Other than copying the binary somewhere into `PATH`, no further installation steps are required. Compatible with and tested on Linux and FreeBSD.

Most configuration is handled via ZFS properties on datasets and can be overridden with environment variables. The formerly required YAML configuration file has become optional and now only covers the definition of location aliases. SSH-specific options have been removed entirely and are left to SSH configuration.

Locations take over as a powerful concept to describe sources and targets for operations, including multiple hop ssh connections, specific user accounts and root datasets.

Renamed CLI sub-commands:

- `clean`: `free`
- `tree`: `ls` with overall more functionality
- `snap`: unchanged
- `backup`: `sync`

Features (yet) missing compared to 0.1:

- `init` sub-command
- translation (i18n)
- GUI
- Python API
- Peaceful coexistence with `zfs-auto-snapshot`
- Cleanup on target side

Other:

- FEATURE: FreeBSD support, assuming OpenZFS
- FEATURE: All commands can produce JSON output with `-j`.
- FEATURE: Locations strings including routes, user names and root datasets
- FEATURE: Snapshot names based on custom format strings
- FEATURE: Built-in support for optional `xz`-compressed transfers
- FEATURE: Optional bandwidth limit on transfers to avoid congestion in overall bandwidth-limited settings
- FEATURE: Optional insecure but fast transfers via `nc`
- DEV: Test suite running on dedicated VMs, both Linux and FreeBSD

## 0.1.0 (2026-XX-XX)

**CAUTION**: The configuration layout changed, effectively **BREAKING BACKWARDS COMPATIBILITY** for most use-cases!

With this release, the Python implementation is sunset and may only receive bugfixes. For new deployments, please use the Rust-reimplementation as of version >= 0.2.

The `keep_backlog` configuration parameter, which could previously be both a boolean and an integer, is now only allowed to be an integer. If no snapshots shall be kept on the target side, it must now be set to `0`. If all snapshots shall be kept on the target side (default behavior), it must now be set to `-1`. Arbitrary numbers greater than `0` remains unaffected by this change.

`abgleich` will use **semantic versioning** from now on. Breaking changes will be indicated by increasing the second version number, the minor version. Going for example from `0.0.x` to `0.1.y` or going from `0.1.x` to `0.2.y` therefore indicates a breaking change.

- FEATURE: `abgleich` can be initialized i.e. told to generate an initial configuration via a simple CLI wizard by running `abgleich init {filename}.yaml`.
- FEATURE: Introduced a debug mode, activated by setting the `ABGLEICH_DEBUG` environment variable to `1`. Debug features were previously hard-coded activated, making `abgleich` now with debug features deactivated by default much faster.
- FIX: Improved error handling by not passing snapshots failed to send completely to stdout.
- DEV: Moved from `setuptools` for packaging to `pyproject.toml` via `flit`.
- DEV: Added rudimentary test suite.

## 0.0.8 (2022-01-21)

- FEATURE: `zfs-auto-snapshot` can be told to ignore backup datasets on the target side, see #3.
- FEATURE: `samba` can optionally be told to NOT share/expose backup datasets on the target side, see #4.
- FEATURE: `ssh`-port on source and target becomes configurable, see #22.
- FEATURE: New configuration fields for `source` and `target` each: `processing`. They can carry shell commands for pre- and post-processing of data before and after it is transferred via ssh. This enables the use of e.g. `lzma` or `bzip2` as a custom transfer compression beyond the compression capabilities of `ssh` itself. See #23.
- FEATURE: `abgleich clean` can also remove snapshots on `target` but only if they are not part of the current overlap with `source`. The behavior can be controlled via the new `keep_backlog` configuration option, see #24 and #25.
- FEATURE: Configuration module contains default values for parameters, making it much easier to write lightweight configuration files, see #28. The configuration parser now also provides much more useful output.
- FEATURE: `abgleich tree` and `abgleich compare` highlight ignored datasets.
- FEATURE: Significantly more flexible shell command wrapper and, as a result, cleaned up transaction handling.
- FEATURE: Python 3.9 and 3.10 compatibility.
- FIX: Many cleanups in code base, enabling future developments.

## 0.0.7 (2020-08-05)

- FIX: `tree` now properly checks if source or target is up, depending on what a user wants to see, see #20.
- FIX: All `abgleich` commands can properly initialize (instead of crashing) if the target tree is empty, see #19.
- FIX: `tree` shows message if there is no tree instead of crashing, see #18.

## 0.0.6 (2020-07-24)

- FIX: Development installs with `make install` do no longer fail, see #17.
- FIX: Python up to 3.7.1 does not handle type checks for `OrderedDict` properly and either causes exceptions or crashes. Fixed with workaround, see #16.

## 0.0.5 (2020-07-24)

- FEATURE: Version shown in GUI
- FEATURE: Version exposed through `--version` option on command line
- FEATURE: While `{zpool}{/{prefix}}` is included in all operations by default, this can be deactivated by setting the new `include_root` configuration option to `no`, see #14.
- FIX: If a remote host is not up, provide a proper error and fail gracefully, see #15.

## 0.0.4 (2020-07-22)

- FEATURE: Improved labels in wizard GUI
- FEATURE: Significantly improved German translation
- FIX: Importing `CLoader` and `CDumper` from `pyyaml` caused crashes if they were not present in `pyyaml` packages, see #2.
- FIX: The `mountpoint` property of ZFS datasets is no longer assumed to be present at all (set or unset). This allows to handle ZVOLs without crashing, see issue #6.
- FIX: Versions 0.0.2 and 0.0.3 were completely ignoring ZVOLs when looking for snapshot tasks, see issue #10.

## 0.0.3 (2020-07-19)

- FEATURE: Added wizard GUI for backup tasks (`snap`, `backup`, `cleanup`)
- FEATURE: Added new configuration options (`always_changed`, `written_threshold`, `check_diff`) for detecting snapshot tasks
- FEATURE: CLI and GUI translations (i18n)
- FIX: Added missing type checks

## 0.0.2 (2020-07-14)

- FEATURE: New, fully object oriented base library
- FEATURE: Python 3.8 support added
- FIX: `cleanup` does not delete snapshots on source if they are not present on target.
- FIX: Wait for ZFS's garbage collection after `cleanup` for getting a meaningful value for freed space.
- Dropped Python 3.5 support

## 0.0.1 (2019-08-05)

- Initial release.
