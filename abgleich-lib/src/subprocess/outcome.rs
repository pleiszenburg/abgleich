use std::process::ExitStatus;

use super::errors::SubprocessError;

pub struct Outcome {
    stdout: Vec<u8>,
    stderr: Vec<u8>,
    status: ExitStatus,
}

impl Outcome {
    #[must_use]
    pub const fn new(stdout: Vec<u8>, stderr: Vec<u8>, status: ExitStatus) -> Self {
        Self {
            stdout,
            stderr,
            status,
        }
    }

    #[must_use]
    pub const fn get_exitstatus_ref(&self) -> &ExitStatus {
        &self.status
    }

    pub fn stdout_as_str_ref(&self) -> Result<&str, SubprocessError> {
        str::from_utf8(&self.stdout).map_err(SubprocessError::ProcStreamDecodingError)
    }

    pub fn stderr_as_str_ref(&self) -> Result<&str, SubprocessError> {
        str::from_utf8(&self.stderr).map_err(SubprocessError::ProcStreamDecodingError)
    }

    #[must_use]
    pub fn success(&self) -> bool {
        self.status.success()
    }
}
