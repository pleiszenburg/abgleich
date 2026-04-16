use std::fmt::Display;
use std::io::Error as IoError;
use std::str::Utf8Error;

use thiserror::Error as ThisError;

#[derive(Debug)]
pub enum Stream {
    Stdout,
    Stderr,
}

impl Display for Stream {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Stderr => write!(f, "stderr"),
            Self::Stdout => write!(f, "stdout"),
        }
    }
}

#[derive(ThisError, Debug)]
pub enum SubprocessError {
    #[error("entry route does not support custom user, username '{0}' was provided")]
    EntryRouteUser(String),
    #[error("failed to run subprocess: {command}")]
    Run{
        command: String,
        source: IoError
    },
    #[error("failed to spawn subprocess: {command}")]
    Spawn{
        command: String,
        source: IoError,
    },
    #[error("string contains null byte")]
    ProcNullByte,
    #[error("failed to attach to stream {stream} of subprocess: {command}")]
    StreamAttach{
        command: String,
        stream: Stream,
    },
    #[error("failed decode stream {stream} into valid utf8: {command}")]
    StreamDecoding{
        command: String,
        source: Utf8Error,
        stream: Stream,
    },
    #[error("failed to read from {stream} of subprocess: {command}")]
    StreamReadError{
        command: String,
        source: IoError,
        stream: Stream,
    },
}
