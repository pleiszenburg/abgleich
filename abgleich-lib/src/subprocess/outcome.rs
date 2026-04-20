use std::process::ExitStatus;

use super::errors::{Stream, SubprocessError};

pub enum OutcomeSuccess {
    Yes,
    No(String), // reason
}

pub struct Outcome {
    stdout: Vec<u8>,
    stderr: Vec<u8>,
    status: ExitStatus,
    meta: String, // only for error reporting
}

impl Outcome {
    #[must_use]
    pub const fn new(stdout: Vec<u8>, stderr: Vec<u8>, status: ExitStatus, meta: String) -> Self {
        Self {
            stdout,
            stderr,
            status,
            meta,
        }
    }

    #[must_use]
    pub const fn get_exitstatus_ref(&self) -> &ExitStatus {
        &self.status
    }

    pub fn stdout_as_str_ref(&self) -> Result<&str, SubprocessError> {
        str::from_utf8(&self.stdout).map_err(|e| SubprocessError::StreamDecoding {
            command: self.meta.clone(),
            source: e,
            stream: Stream::Stdout,
        })
    }

    pub fn stderr_as_str_ref(&self) -> Result<&str, SubprocessError> {
        str::from_utf8(&self.stderr).map_err(|e| SubprocessError::StreamDecoding {
            command: self.meta.clone(),
            source: e,
            stream: Stream::Stderr,
        })
    }

    #[must_use]
    pub fn success(&self) -> OutcomeSuccess {
        if self.status.success() {
            return OutcomeSuccess::Yes;
        }
        OutcomeSuccess::No(self.status.code().map_or_else(
            || "terminated by signal".to_string(),
            |code| format!("exited with code {code}"),
        ))
    }
}
