# AGENTS.md — abgleich project guide for LLM agents

> **Onboarding prompt** (paste at the start of a new session):
> "Read `AGENTS.md` in the project root thoroughly before doing anything else. It is the authoritative onboarding document for this codebase. Follow all conventions it describes."

---

## Project overview

**abgleich** is a ZFS management and synchronization CLI tool. It manages/backs up ZFS datasets across multiple machines, including over SSH with multi-hop routes. Written in Rust 2024 edition. The binary is called `abgleich`.

---

## Repository layout

```
abgleich-cli/           thin binary crate; main.rs → abgleich_lib::cli::entrypoint()
abgleich-lib/           library crate; all logic; feature-gated "cli" for clap/tracing-subscriber
docs/                   Sphinx docs; development.rst is the key dev guide
docs/top-level.just     doc build recipes (imported by root justfile)
tests/                  Python pytest suite
tests/lib/              test infrastructure (~31 modules)
tests/vagrant/          Vagrant + VirtualBox VM management (linux/, freebsd/, keys/)
tests/vagrant/top-level.just  VM control recipes (imported by root justfile)
justfile                root command runner; imports docs/ and tests/vagrant/ justfiles
bin/package.sh          packaging script
```

---

## Languages & tooling

| Tool | Purpose |
|---|---|
| Rust 2024 edition | core implementation |
| `just` ≥ 1.46 | command runner everywhere (host + VMs) |
| `cross` | cross-compilation (needs docker or podman) |
| `upx` | binary compression for Linux musl releases |
| `cargo-hack` | feature flag powerset checks |
| `clippy` pedantic+nursery | linting (aspired standard) |
| Python ≥ 3.12 | test suite |
| `pytest` | test runner |
| `vagrant` + `virtualbox` | test VM management |
| Sphinx | documentation |

Install Python test deps: `pip install -vr tests/requirements.txt`
Install doc deps: `pip install -vr docs/requirements.txt`

---

## Build system (`justfile`)

```bash
just build [TARGET]           # debug build via cross (default: x86_64-unknown-linux-musl)
just release [TARGET]         # release build + upx for Linux targets
just clippy                   # cargo clippy pedantic+nursery
just test-internal            # cargo test (internal Rust unit tests)
just test-features            # cargo-hack: all feature flag permutations
just fmt                      # cargo fmt
just clean-build              # remove build artifacts
just clean-dist               # remove dist/
just dist                     # package all targets
just docs-build [TARGET]      # build Sphinx docs (default: html)
just clean-docs               # remove built docs
```

Build targets: `x86_64-unknown-linux-musl` (default), `x86_64-unknown-linux-gnu`, `x86_64-unknown-freebsd`

**Local musl build without cross** (Linux):
```bash
rustup target add x86_64-unknown-linux-musl
sudo apt install musl-tools
```

**Cargo workspace** (`Cargo.toml`):
- Members: `abgleich-cli`, `abgleich-lib`
- Release profile: `lto=true`, `opt-level="z"`, `strip=true`, `panic="abort"`

**`abgleich-lib` features**: `cli = ["dep:clap", "dep:tracing-subscriber"]`

---

## Rust code structure (`abgleich-lib/src/`)

```
cli/            clap CLI; command.rs defines Commands enum; dispatch.rs routes commands
config/         YAML config detection + parsing; location.rs + route.rs
engine/         core ZFS logic (Engine, Apool, Dataset, Snapshot, comparison/, property/)
output/         table and storage display
subprocess/     Command, CommandChain, Outcome, Proc
transaction/    Transaction types, TransactionList, run_cli()
sys/            env, logging, errors
traits/         FromSerializable, ToSerializable, PathToString, Traverse
consts.rs       all constants and default values
```

### CLI subcommands (`cli/command.rs` → `Commands` enum)

| Subcommand | Flags | Args |
|---|---|---|
| `ls` | `-j/--json` | `[location]` (optional) |
| `snap` | `-j`, `-y/--yes`, `-f/--force` | `location` |
| `sync` | `-j`, `-y`, `-f`, `-d/--direct`, `-r/--rate-limit` (e.g. `10m`,`500k`), `-x/--compress` (level 0–9, default 5) | `source target` |
| `free` | `-j`, `-y`, `-f` | `source target` |
| `version` | — | — |

`--compress` without value defaults to level 5; omitting `--compress` entirely uses `zfs send -c`.

### Location format

```
[route:][user%]root
```
- `route`: optional SSH hop(s), e.g. `gateway/backupbox`
- `user`: optional ZFS command user; `root` → sudo
- `root`: root dataset; trailing `/` excludes root, includes descendants only
- Example: `gateway/backupbox:backupuser%tank/some/dataset`

### Config detection order

1. `ABGLEICH_CONFIG` env var
2. `./abgleich.yaml`
3. `~/.abgleich.yaml`
4. `/etc/abgleich.yaml`

### ZFS user properties (`abgleich:*`)

| Property | Type | Default | Meaning |
|---|---|---|---|
| `format` | string | `abgleich_%Y-%m-%dT%H:%M:%S:%3f_backup` | snapshot name format |
| `overlap` | int | `2` | snapshots to keep on source (-1 = all) |
| `diff` | bool | `true` | show diffs |
| `threshold` | u64 bytes | `12_582_912` | min data size to trigger sync |
| `snap` | enum | `changed` | `always` / `changed` / `never` |
| `sync` | bool | `true` | allow syncing |

### Subprocess abstraction

`Command` is immutable and chainable:
```rust
Command::new(program, args)?
    .with_user("backupuser")?   // → sudo -u backupuser ...
    .on_route(&route)?          // → ssh hop1 ssh hop2 ...
    .run()
```
`CommandChain` represents a pipe: `.begin(cmd)?.chain(cmd)?.run()`.

### Transaction system

Transaction types: `CreateSnapshot`, `DestroySnapshot`, `TransferInitial`, `TransferIncremental`, `Diff`, `Inventory`, `Which`, `ZpoolList`.

`TransactionList::run_cli()` handles user prompts (`-y` skips), table/JSON output (`-j`), force mode (`-f`).

### Code style

- Rust 2024 edition; passes `clippy` pedantic+nursery (aspirational)
- `thiserror` for error types; every module has its own `errors.rs`
- `#[must_use]` on getters; explicit `Clone` impls
- Internal unit tests in `#[cfg(test)] mod tests` blocks in the same file

---

## Testing

### Overview

Two test types:
1. **CLI integration tests** — Python pytest, run inside VMs, covering all subcommands
2. **Internal Rust tests** — `cargo test`, test parser functions etc. (`just test-internal`)
3. **Feature flag tests** — `cargo-hack` (`just test-features`)

### VM architecture

4 VMs across 2 platforms, managed by Vagrant + VirtualBox:

| VM | IP | Role |
|---|---|---|
| `linux-a` | 192.168.56.10 | primary Linux test node (runs pytest) |
| `linux-b` | 192.168.56.11 | secondary Linux node |
| `freebsd-a` | 192.168.56.20 | primary FreeBSD test node |
| `freebsd-b` | 192.168.56.21 | secondary FreeBSD node |

- Project root synced to `/project` on all VMs
- Shared Ed25519 keypair: `tests/vagrant/keys/id_ed25519` (gitignored; generated once)
- Passwordless SSH between all VMs on `192.168.56.*`
- Users: `vagrant` (passwordless sudo), `flashheart` (no sudo, used for `zfs allow` tests)
- Snapshot `clean` saved after provisioning for fast reset

### VM lifecycle commands

```bash
just setup linux          # generate keys, provision 2 Linux VMs, save clean snapshot
just setup freebsd        # same for FreeBSD
just reset linux          # halt + restore to clean snapshot + boot
just halt linux           # graceful shutdown
just test linux           # build debug binary + run full pytest suite on linux-a
just test freebsd         # same on freebsd-a
just debug linux EXPR     # run pytest -k EXPR on linux-a
just debug freebsd EXPR     # run pytest -k EXPR on freebsd-a
```

### Test session layout (per VM)

- Session root: `/tmp/session`
- Config file: `/tmp/session/abgleich.yaml` (written by test infrastructure)
- Zpool backing files: `/tmp/session/{name}.bin` (default 1 GiB)

### Environment variables

| Variable | Effect |
|---|---|
| `ABGLEICH_TEST_VERBOSE=1` | verbose test output |
| `ABGLEICH_TEST_RELEASE=1` | test release builds |
| `ABGLEICH_TEST_TARGET` | override build target (e.g. `x86_64-unknown-linux-gnu`) |
| `ABGLEICH_TEST_LOGTODISK=1` | write abgleich logs to disk during tests |
| `ABGLEICH_LOGLEVEL` | 0=trace, 10=debug, 20=info, 30=warn (default) |
| `RUST_BACKTRACE` | passed through to abgleich |

### Python test library (`tests/lib/`)

All exports are re-exported from `tests/lib/__init__.py`. Key classes:

**`TestConfig`** — hierarchical config dict with env var overrides. Keys like `nodes/current_a/zpools`. The `abgleich` sub-key holds the `Config` passed to abgleich.

**`Environment`** — pytest decorator that wraps test function with `Context` setup/teardown. Accepts one or more `TestConfig` instances (parametrize via multiple).

**`Context`** — central test manager:
- `ctx.abgleich(Subcmd.snap, "-y", "root%foo")` → runs abgleich, returns `Result`
- `ctx.abgleich(..., background=True)` → returns awaitable callable for concurrent tests
- `ctx.parse_transactions(res.stdout, json=bool)` → `List[Transaction]`
- `ctx.parse_ls_pools(...)` → `List[ApoolDescription]`
- `ctx.parse_ls_tree(...)` → `List[EntryDescription]`
- `ctx.reload()` → refresh ZFS state for validation
- `ctx[Host.localhost]["poolname"]` → `Zpool`
- `ctx[Host.localhost]["poolname"] / "child"` → `Filesystem`

**`Node`** — VM node; `node["poolname"]` → `Zpool`.

**`Zpool(Filesystem)`** — ZFS zpool backed by `.bin` file.

**`Filesystem(Dataset)`** — ZFS filesystem; `fs / "child"` → child, `fs.snapshots`, `fs.aproperties`.

**`Volume(Dataset)`** — ZFS volume.

**`AProperties`** — wraps `abgleich:*` properties; `Snap` enum: `always`, `changed`, `never`.

**`Host`** enum: `localhost` (= `current_a`), `current_b`, `other_a`, `other_b`.

**`Subcmd`** enum: `none`, `free`, `ls`, `snap`, `sync`, `version`.

**`Transaction`** hierarchy: `CreateSnapshotTransaction`, `DestroySnapshotTransaction`, `TransferInitialTransaction`, `TransferIncrementalTransaction`, `DiffTransaction`, etc. Dispatch via `Transaction.from_fields(**row)`.

**`Command`** — subprocess runner: `.on_host(host)`, `.with_sudo()`, `.with_user(name)`, `.with_env(env)`, `.run(cwd, timeout, stdin)`.

**Output parsing**: Table output is pipe-delimited `| col | col |`; JSON output is newline-delimited JSON objects. ANSI codes are stripped before table parsing.

### Writing tests

```python
@pytest.mark.parametrize("json", (False, True))
@Environment(TestConfig(
    zpools = [Zpool(name = "foo", aproperties = AProperties.from_defaults(),
                    datasets = [Filesystem(name = "one")])],
))
def test_example(ctx: Context, json: bool):
    args = ("-j",) if json else tuple()
    res = ctx.abgleich(Subcmd.snap, *args, "-y", "root%foo")
    res.assert_exitcode(0)
    transactions = ctx.parse_transactions(res.stdout, json=json)
    assert len(transactions) == 2
    ctx.reload()
    assert len(set(ctx[Host.localhost]["foo"].snapshots)) == 1
```

Existing test files: `test_help.py`, `test_ls_pools.py`, `test_ls_tree.py`, `test_snap.py`, `test_sync.py`, `test_sync_compress.py`, `test_sync_ratelimit.py`, `test_sync_route.py`, `test_free.py`, `test_force.py`.

---

## Documentation

- Source: `docs/source/` (reStructuredText)
- `docs/source/development.rst` — authoritative development guide
- Build: `just docs-build` → `docs/build/html/`
- `just docs-cli` — regenerates CLI reference from binary output
- Python venv required; install: `pip install -vr docs/requirements.txt`

---

## Maintenance prompt

To update this file without losing critical information, use this prompt:

> "Read `AGENTS.md` in full. Then read the following files to check for changes since the last update: `docs/source/development.rst`, `justfile`, `abgleich-lib/Cargo.toml`, `abgleich-lib/src/cli/command.rs`, `abgleich-lib/src/consts.rs`, `tests/lib/__init__.py`, and any new test files in `tests/`. Update `AGENTS.md` to reflect any changes. Preserve all existing sections. Add new sections only if genuinely new concepts appeared. Keep the style condensed — fewer words is better. Do not remove the onboarding prompt, the maintenance prompt, or the missing-information section (update it instead)."
