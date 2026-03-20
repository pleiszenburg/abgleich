# Vagrant Test Environment

Two-platform, four-VM test environment for ZFS management tooling. Both
Linux (Ubuntu 24.04) and FreeBSD 14 guests are supported. All VMs can reach
each other over passwordless SSH and are restorable to a clean snapshot.

## Prerequisites

| Tool              | Tested with | Install                                                            |
|-------------------|-------------|--------------------------------------------------------------------|
| VirtualBox        | 6.x         | https://www.virtualbox.org/                                        |
| Vagrant           | 2.4+        | https://www.vagrantup.com/                                         |
| just              | ≥ 1.18      | `cargo install just` or OS package                                 |
| ssh-keygen        | (any)       | Ships with OpenSSH                                                 |

## Architecture

```
 ├─ linux-a    192.168.56.10  ┐
 │      ↕ SSH (passwordless)  ├ Ubuntu 24.04 · ZFS via apt · Python venv in ~/venv
 ├─ linux-b    192.168.56.11  ┘
 │                    ↕ SSH (passwordless, same keypair)
 ├─ freebsd-a  192.168.56.20  ┐
 │      ↕ SSH (passwordless)  ├ FreeBSD 14 · ZFS in base · Python venv in ~/venv
 └─ freebsd-b  192.168.56.21  ┘
```

All four VMs share a single Ed25519 keypair (`keys/`) and have each other's
hostnames in `/etc/hosts`, so cross-platform SSH (`ssh freebsd-a` from
`linux-b`, etc.) works without any extra configuration.

Both environments use **linked clones** to minimise disk usage.

## Layout

```
vagrant/
├── .gitignore
├── keys/                 ← shared SSH keypair (gitignored)
│   └── justfile          ← key generation recipe
├── top-level.just        ← import this into project's root justfile
├── linux/                ← Ubuntu 24.04 environment
│   ├── Vagrantfile
│   ├── justfile
│   └── provision/
│       ├── base.sh
│       └── deploy_ssh_keys.sh
├── freebsd/              ← FreeBSD 14 environment
│   ├── Vagrantfile
│   ├── justfile
│   └── provision/
│       ├── base.sh
│       └── deploy_ssh_keys.sh
└── README.md             ← this file
```

## VM recipes

Run from within `vagrant/linux/` or `vagrant/freebsd/`, or via
`just vm <platform> <recipe>` from the project root.

| Recipe              | Description                                     |
|---------------------|-------------------------------------------------|
| `just setup`        | Create VMs and take "clean" snapshot            |
| `just up`           | Start VMs                                       |
| `just halt`         | Graceful shutdown                               |
| `just test`         | Run tests on primary node (VMs assumed running) |
| `just reset`        | Restore snapshot + wait for SSH                 |
| `just snapshot`     | Save "clean" snapshot                           |
| `just restore`      | Revert to "clean" snapshot                      |
| `just ssh <node>`   | Interactive shell on a node                     |
| `just verify-ssh`   | Test bidirectional SSH                          |
| `just list-disks`   | Show block devices                              |
| `just both <cmd>`   | Run a command on both nodes                     |
| `just destroy`      | Tear down VMs                                   |
| `just clean`        | Tear down VMs                                   |
| `just provision`    | Re-run provisioning only                        |
| `just status`       | Show VM status                                  |

## Top-level justfile integration

`top-level.just` is designed to be imported into a project root justfile:

```just
import 'vagrant/top-level.just'
```

This single line exposes all standard top-level recipes in the project
namespace: `generate-keys`, `setup`, `test`, `reset`, `pytest`, `clean`,
`halt`, and `vm`. Requires **just ≥ 1.18**.

Internally, `source_directory()` is used throughout `top-level.just` so that
all paths resolve relative to `vagrant/` regardless of where the importing
justfile lives. No path configuration is needed.

If you need to support an older version of just, or need per-project
customisation of individual recipes, copy the contents of `top-level.just`
into your root justfile and edit as needed.

The top-level recipes assume the project root contains:

- `tests/` – pytest test suite (invoked by `just pytest` → `pytest -s tests/`)
- `vagrant/` – this directory, as a submodule or direct checkout

## Shared filesystem

The project root is mounted as `/project` inside each VM:

- **Linux**: VirtualBox shared folders (default synced folder type)
- **FreeBSD**: rsync (VBoxSF is unreliable on FreeBSD guests); `vagrant rsync`
  is run automatically before each test cycle

## Python virtual environment

Each VM has a Python virtual environment at `/home/vagrant/venv` with all
packages from `requirements.txt` pre-installed at provision time. The venv
is activated automatically on login via `.profile`. If `requirements.txt`
changes, rebuild with `just vm <platform> destroy && just setup <platform>`.

## Open ports

Port **18432** (TCP and UDP) is opened on all four VMs during provisioning.
If a firewall is found to be active at provision time, a rule permitting
inbound traffic on this port is added while leaving the rest of the firewall
configuration intact:

- **Linux** (`ufw`): `ufw allow 18432/tcp` and `ufw allow 18432/udp`
- **FreeBSD** (`pf`): `pass in proto { tcp udp } to port 18432 keep state`
  appended to `/etc/pf.conf`, followed by `pfctl -f`
- **FreeBSD** (`ipfw`): runtime rules added via `ipfw add allow`; also
  appended to `/etc/ipfw.rules` if that file exists, for persistence

On the default base boxes (`bento/ubuntu-24.04`, `generic/freebsd14`) no
firewall is active by default, so provisioning is a no-op for this step.

## User accounts

Root SSH login is disabled on all VMs. The `vagrant` user has passwordless
`sudo`.

There is another user, `flashheart`, which can not use `sudo`, without
home folder and password. It can be used to test `zfs allow` and its side
effects. `vagrant` can use `sudo -u flashheart` to invoke commands through
this user account.

## Adding real tests

Add test files under `tests/` following the `test_*.py` / `test_*` naming
convention and update `requirements.txt` with any new dependencies. Tests run
inside the primary node via `just test`, which calls `just pytest` inside the
VM.

Tests should confine side-effects to `/tmp/session` inside the VMs and clean
up that directory themselves.

## SSH

- The keypair in `keys/` is for the isolated test network only; never reuse
  it outside this test environment.
- SSH host-key checking is disabled for the `192.168.56.*` subnet inside the
  VMs (`StrictHostKeyChecking no`, `UserKnownHostsFile /dev/null`) so
  snapshot restores do not cause connection failures.
