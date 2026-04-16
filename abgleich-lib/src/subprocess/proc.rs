use std::ffi::OsStr;
use std::io::Read;
use std::process::{Child, Command as StdCommand, Stdio};

use super::command::Command;
use super::errors::{SubprocessError, Stream};
use super::outcome::Outcome;

pub struct Proc {
    child: Child,
    stdout_taken: bool,
    meta: String,  // for errors only
}

impl Proc {
    pub fn from_command(command: &Command, stdin: Option<Stdio>) -> Result<Self, SubprocessError> {
        let meta = command.to_string();
        let mut child = StdCommand::new(OsStr::new(command.get_program_ref()));
        let child = child
            .args(command.iter_arguments())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());
        let child = match stdin {
            Some(stdin) => child.stdin(stdin),
            _ => child,
        };
        Ok(Self {
            child: child
                .spawn()
                .map_err(|e| SubprocessError::Spawn{command: meta.clone(), source: e})?,
            stdout_taken: false,
            meta,
        })
    }

    pub fn take_stdout(mut self) -> Result<Stdio, SubprocessError> {
        self.stdout_taken = true;
        Ok(Stdio::from(
            self.child
                .stdout
                .take()
                .ok_or(SubprocessError::StreamAttach{command: self.meta, stream: Stream::Stdout})?,
        ))
    }

    pub fn communicate(mut self) -> Result<Outcome, SubprocessError> {
        let mut stdout_buffer: Vec<u8> = Vec::new();
        if !self.stdout_taken {
            let child_stdout = self
                .child
                .stdout
                .as_mut()
                .ok_or_else(|| SubprocessError::StreamAttach{command: self.meta.clone(), stream: Stream::Stdout})?;
            child_stdout
                .read_to_end(&mut stdout_buffer)
                .map_err(|e| SubprocessError::StreamReadError{source: e, stream: Stream::Stdout, command: self.meta.clone()})?;
        }
        let mut stderr_buffer: Vec<u8> = Vec::new();
        let child_stderr = self
            .child
            .stderr
            .as_mut()
            .ok_or_else(|| SubprocessError::StreamAttach{command: self.meta.clone(), stream: Stream::Stderr})?;
        child_stderr
            .read_to_end(&mut stderr_buffer)
            .map_err(|e| SubprocessError::StreamReadError{source: e, stream: Stream::Stderr, command: self.meta.clone()})?;
        let status = self
            .child
            .wait()
            .map_err(|e| SubprocessError::Run{command: self.meta.clone(), source: e})?;
        Ok(Outcome::new(stdout_buffer, stderr_buffer, status, self.meta))
    }
}
