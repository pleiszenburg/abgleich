use crate::config::{Location, Route};

use super::command::Command;
use super::errors::SubprocessError;
use super::outcome::Outcome;
use super::proc::Proc;

/// A pipeline stage. Either a fully-routed single command (already wrapped
/// with ssh/sudo via `on_location`) or a co-located group of plain commands
/// that share one host and one optional user identity.
enum Stage {
    /// A fully-routed command, rendered as-is into the pipeline string.
    Single(Command),
    /// A set of plain (unrouted) commands that run together on `route` under
    /// `user`. Rendered as:
    ///  - one command  → `[sudo[-u user]] cmd`, then SSH-wrapped if route non-empty
    ///  - many commands → `[sudo[-u user]] bash -c 'set -o pipefail; cmd1 | cmd2'`,
    ///                    SSH-wrapped if route non-empty
    Group {
        route: Route,
        user: Option<String>,
        commands: Vec<Command>,
    },
}

impl Stage {
    fn render(&self) -> Result<String, SubprocessError> {
        match self {
            Stage::Single(cmd) => Ok(cmd.to_string()),
            Stage::Group { route, user, commands } => {
                debug_assert!(!commands.is_empty(), "Group stage must have at least one command");
                let inner_cmd = if commands.len() == 1 {
                    commands[0].clone()
                } else {
                    // Wrap multiple commands in bash so pipefail applies within
                    // this co-located sub-pipeline.
                    let pipe_str = commands
                        .iter()
                        .map(ToString::to_string)
                        .collect::<Vec<_>>()
                        .join(" | ");
                    let shell_cmd = format!("set -o pipefail; {pipe_str}");
                    Command::new("bash".to_string(), vec!["-c".to_string(), shell_cmd])?
                };
                let user_cmd = match user.as_deref() {
                    Some(u) => inner_cmd.with_user(u)?,
                    None => inner_cmd,
                };
                user_cmd.on_route(route).map(|c| c.to_string())
            }
        }
    }
}

pub struct CommandChain {
    stages: Vec<Stage>,
    entry_route: Route,
    /// Optional background stage started before the main pipeline.  Used by
    /// the insecure (nc) transfer path: the receiver (`nc -l | zfs receive`)
    /// is launched in the background first, then the sender connects to it.
    /// Rendered as `(BG) & BGPID=$!; sleep 1; FG; wait $BGPID` inside the
    /// outer `bash -c '…'`.
    background: Option<Stage>,
}

impl CommandChain {
    #[must_use]
    pub fn begin(command: Command) -> Self {
        Self {
            stages: vec![Stage::Single(command)],
            entry_route: Route::from_localhost(),
            background: None,
        }
    }

    #[must_use]
    pub fn pipe(mut self, command: Command) -> Self {
        self.stages.push(Stage::Single(command));
        self
    }

    /// Start a chain with a co-located group of commands on `location`.
    ///
    /// Commands must be plain (not pre-routed). Routing and user escalation
    /// are applied during rendering.  Use this when multiple commands must
    /// share one SSH connection (e.g. `zfs send | pv | xz` on the source
    /// host).
    #[must_use]
    pub fn begin_group(location: &Location, commands: Vec<Command>) -> Self {
        Self {
            stages: vec![Stage::Group {
                route: location.get_route_ref().clone(),
                user: location.get_user_ref().map(str::to_string),
                commands,
            }],
            entry_route: Route::from_localhost(),
            background: None,
        }
    }

    /// Set a background stage that is started before the main pipeline with a
    /// 1-second delay before the foreground is launched.  The background
    /// process is waited on after the foreground completes.
    ///
    /// Used by the insecure (nc) transfer path: the receiver group is set as
    /// the background so that `nc -l` is listening before the sender connects.
    #[must_use]
    pub fn with_background_group(mut self, location: &Location, commands: Vec<Command>) -> Self {
        self.background = Some(Stage::Group {
            route: location.get_route_ref().clone(),
            user: location.get_user_ref().map(str::to_string),
            commands,
        });
        self
    }

    /// Append a co-located group stage.
    #[must_use]
    pub fn pipe_group(mut self, location: &Location, commands: Vec<Command>) -> Self {
        self.stages.push(Stage::Group {
            route: location.get_route_ref().clone(),
            user: location.get_user_ref().map(str::to_string),
            commands,
        });
        self
    }

    #[must_use]
    pub fn with_entry_route(mut self, route: Route) -> Self {
        self.entry_route = route;
        self
    }

    fn to_pipe_string(&self) -> Result<String, SubprocessError> {
        let parts: Result<Vec<String>, SubprocessError> =
            self.stages.iter().map(Stage::render).collect();
        Ok(parts?.join(" | "))
    }

    // Reduce the chain to a single Command that can be spawned.
    //
    // Fast path: a chain with exactly one local Single stage needs no shell
    // wrapper — the command is spawned directly.  This covers the common case
    // of single-command transactions (create/destroy snapshot, inventory, …).
    //
    // All other cases (multiple stages, a Group stage, or a non-empty
    // entry_route) are wrapped in `bash -c 'set -o pipefail; …'` and
    // optionally SSH-routed through the entry host.  Using bash everywhere
    // avoids having to manage a multi-process ProcChain and lets the shell
    // handle pipe wiring transparently, including the nested sub-pipelines
    // produced by Group stages for rate limiting and compression.
    fn to_command(&self) -> Result<Command, SubprocessError> {
        // Fast path: single local Single stage with no background.
        if self.background.is_none() && self.stages.len() == 1 && self.entry_route.is_empty() {
            if let Stage::Single(cmd) = &self.stages[0] {
                return Ok(cmd.clone());
            }
        }
        let fg_str = self.to_pipe_string()?;
        let shell_cmd = if let Some(bg) = &self.background {
            let bg_str = bg.render()?;
            // Start receiver in background, wait 1 s for nc to bind, run
            // sender, then wait for the background process to finish cleanly.
            format!("set -o pipefail; ({bg_str}) & BGPID=$!; sleep 1; {fg_str}; wait $BGPID")
        } else {
            format!("set -o pipefail; {fg_str}")
        };
        Command::new("bash".to_string(), vec!["-c".to_string(), shell_cmd])?
            .on_route(&self.entry_route)
    }

    pub fn run(&self) -> Result<Outcome, SubprocessError> {
        let cmd = self.to_command()?;
        Proc::from_command(&cmd, None)?.communicate()
    }
}

#[allow(clippy::to_string_trait_impl)]
impl ToString for CommandChain {
    fn to_string(&self) -> String {
        self.to_command()
            .expect("infallible: validated commands contain no null bytes")
            .to_string()
    }
}

#[cfg(test)]
mod tests {
    use std::str::FromStr;

    use crate::config::{Location, Route};

    use super::super::command::Command;
    use super::*;

    fn cmd(program: &str, args: &[&str]) -> Command {
        Command::new(
            program.to_string(),
            args.iter().map(|s| s.to_string()).collect(),
        )
        .unwrap()
    }

    fn route(s: &str) -> Route {
        Route::from_str(s).unwrap()
    }

    fn loc(s: &str) -> Location {
        Location::from_str(s).unwrap()
    }

    // ── Fast path: single local Single stage ──────────────────────────────

    #[test]
    fn single_local_single_stage_no_bash() {
        // A lone local command is NOT wrapped in bash.
        let chain = CommandChain::begin(cmd("zfs", &["snapshot", "tank@snap"]));
        assert_eq!(chain.to_string(), "zfs snapshot tank@snap");
    }

    #[test]
    fn single_remote_single_stage_no_outer_bash() {
        // A lone SSH-routed Single stage is also not wrapped in bash.
        let routed = cmd("zfs", &["snapshot", "tank@snap"])
            .on_hosts(&["host-a"])
            .unwrap();
        let chain = CommandChain::begin(routed);
        assert_eq!(chain.to_string(), "ssh host-a 'zfs snapshot tank@snap'");
    }

    // ── Two-stage Single pipelines ────────────────────────────────────────

    #[test]
    fn two_local_commands_wrapped_in_bash() {
        let chain = CommandChain::begin(cmd("zfs", &["send", "tank@snap"]))
            .pipe(cmd("zfs", &["receive", "backup"]));
        assert_eq!(
            chain.to_string(),
            "bash -c 'set -o pipefail; zfs send tank@snap | zfs receive backup'"
        );
    }

    #[test]
    fn three_local_commands_wrapped_in_bash() {
        let chain = CommandChain::begin(cmd("zfs", &["send", "tank@snap"]))
            .pipe(cmd("pv", &["-q", "-L", "1048576"]))
            .pipe(cmd("zfs", &["receive", "backup"]));
        let s = chain.to_string();
        assert!(s.starts_with("bash -c "), "expected bash prefix: {s}");
        assert!(s.contains("set -o pipefail"), "missing pipefail: {s}");
        assert!(s.contains("pv -q -L 1048576"), "missing pv: {s}");
    }

    // ── entry_route (direct mode) ─────────────────────────────────────────

    #[test]
    fn entry_route_wraps_outer_bash_in_ssh() {
        let send = cmd("zfs", &["send", "tank@snap"]);
        let recv = cmd("ssh", &["tgt", "zfs receive backup"]);
        let chain = CommandChain::begin(send)
            .pipe(recv)
            .with_entry_route(route("linux-a"));
        let s = chain.to_string();
        assert!(s.starts_with("ssh linux-a "), "expected ssh linux-a prefix: {s}");
        assert!(s.contains("set -o pipefail"), "missing pipefail: {s}");
    }

    // ── Group stages ──────────────────────────────────────────────────────

    #[test]
    fn group_single_cmd_renders_like_on_location() {
        // A Group with one command and a remote location must produce the same
        // shell string as cmd.on_location(loc).to_string().
        let location = loc("linux-a:root%tank");
        let send_cmd = cmd("zfs", &["send", "tank@snap"]);

        let via_location = send_cmd.clone().on_location(&location).unwrap().to_string();

        let chain = CommandChain::begin_group(&location, vec![send_cmd]);
        let s = chain.to_string();

        // The chain has one Group stage → the outer bash -c wrapper is present,
        // but the stage itself (the ssh … sudo … part) must match on_location.
        assert!(
            s.contains(&via_location),
            "group single-cmd render '{s}' should contain '{via_location}'"
        );
    }

    #[test]
    fn group_multi_cmd_contains_bash_subpipeline() {
        let src_loc = loc("linux-a:root%tank");
        let tgt_loc = loc("linux-b:root%backup");

        let chain = CommandChain::begin_group(
            &src_loc,
            vec![cmd("zfs", &["send", "tank@snap"]), cmd("xz", &[])],
        )
        .pipe_group(
            &tgt_loc,
            vec![cmd("xz", &["-d"]), cmd("zfs", &["receive", "backup"])],
        );

        let s = chain.to_string();
        assert!(s.contains("set -o pipefail"), "missing outer pipefail: {s}");
        assert!(s.contains("linux-a"), "missing src host: {s}");
        assert!(s.contains("linux-b"), "missing tgt host: {s}");
        assert!(s.contains("xz"), "missing xz: {s}");
        // Both sub-pipelines need their own pipefail inside the bash -c argument.
        assert!(
            s.matches("set -o pipefail").count() >= 3,
            "expected ≥3 pipefail occurrences (outer + 2 sub-pipelines): {s}"
        );
    }

    #[test]
    fn group_with_pv_rate_limit() {
        let src_loc = loc("linux-a:root%pool");
        let tgt_loc = loc("linux-b:root%backup");

        let chain = CommandChain::begin_group(
            &src_loc,
            vec![
                cmd("zfs", &["send", "pool@snap"]),
                cmd("pv", &["-q", "-L", "10485760"]),
                cmd("xz", &[]),
            ],
        )
        .pipe_group(
            &tgt_loc,
            vec![cmd("xz", &["-d"]), cmd("zfs", &["receive", "backup"])],
        );

        let s = chain.to_string();
        assert!(s.contains("pv"), "missing pv: {s}");
        assert!(s.contains("10485760"), "missing rate: {s}");
        assert!(s.contains("xz"), "missing xz: {s}");
        assert!(s.contains("xz -d"), "missing xz -d: {s}");
    }

    // ── Background stage (insecure / nc path) ────────────────────────────

    // Helper: extract the raw bash -c script from a CommandChain.
    // `to_string()` shlex-escapes the script (so `$!` appears as `'$!'`), which
    // is correct for display but inconvenient to assert against.  Pulling the
    // raw argument lets tests verify the actual script content.
    fn raw_script(chain: &CommandChain) -> String {
        let cmd = chain.to_command().unwrap();
        // arguments: ["-c", "<script>"]
        cmd.iter_arguments().nth(1).unwrap().clone()
    }

    #[test]
    fn background_group_renders_with_wait() {
        let src_loc = loc("linux-a:root%tank");
        let tgt_loc = loc("linux-b:root%backup");

        let chain = CommandChain::begin_group(
            &src_loc,
            vec![cmd("zfs", &["send", "tank@snap"]), cmd("nc", &["linux-b", "18432"])],
        )
        .with_background_group(
            &tgt_loc,
            vec![cmd("nc", &["-l", "18432"]), cmd("zfs", &["receive", "backup"])],
        );

        let s = raw_script(&chain);
        assert!(s.contains("& BGPID=$!"), "missing background start: {s}");
        assert!(s.contains("sleep 1"), "missing sleep: {s}");
        assert!(s.contains("wait $BGPID"), "missing wait: {s}");
        assert!(s.contains("linux-a"), "missing src host: {s}");
        assert!(s.contains("linux-b"), "missing tgt host: {s}");
        assert!(s.contains("nc -l 18432"), "missing nc listener: {s}");
        assert!(s.contains("nc linux-b 18432"), "missing nc sender: {s}");
    }

    #[test]
    fn background_group_background_comes_before_foreground() {
        let src_loc = loc("linux-a:root%tank");
        let tgt_loc = loc("linux-b:root%backup");

        let chain = CommandChain::begin_group(
            &src_loc,
            vec![cmd("zfs", &["send", "tank@snap"]), cmd("nc", &["linux-b", "18432"])],
        )
        .with_background_group(
            &tgt_loc,
            vec![cmd("nc", &["-l", "18432"]), cmd("zfs", &["receive", "backup"])],
        );

        let s = raw_script(&chain);
        let bg_pos = s.find("BGPID=$!").expect("no BGPID");
        let sleep_pos = s.find("sleep 1").expect("no sleep");
        let wait_pos = s.find("wait $BGPID").expect("no wait");
        assert!(bg_pos < sleep_pos, "sleep must follow background start");
        assert!(sleep_pos < wait_pos, "wait must follow sleep");
    }

    #[test]
    fn no_background_uses_existing_fast_path() {
        // A single local command must still avoid the bash wrapper.
        let chain = CommandChain::begin(cmd("zfs", &["snapshot", "tank@snap"]));
        assert_eq!(chain.to_string(), "zfs snapshot tank@snap");
    }

    // ── Quoting correctness ───────────────────────────────────────────────

    #[test]
    fn snapshot_name_with_timestamp_survives_quoting() {
        // Snapshot names contain colons; shlex must preserve them verbatim.
        let chain = CommandChain::begin(cmd(
            "zfs",
            &["snapshot", "tank/data@2025-01-15T12:00:00"],
        ));
        let s = chain.to_string();
        assert!(
            s.contains("tank/data@2025-01-15T12:00:00"),
            "snapshot name corrupted by quoting: {s}"
        );
    }

    #[test]
    fn dataset_path_with_slashes_preserved() {
        let chain = CommandChain::begin(cmd("zfs", &["send", "tank/nested/child@snap"]));
        let s = chain.to_string();
        assert!(s.contains("tank/nested/child@snap"), "path lost: {s}");
    }
}
