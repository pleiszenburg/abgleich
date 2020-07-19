# Changes

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
