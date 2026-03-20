use std::io::Error as IoError;
use std::str::Utf8Error;

use shlex::QuoteError;
use thiserror::Error as ThisError;

#[derive(ThisError, Debug)]
pub enum SubprocessError {
    #[error("failed to run subprocess")]
    ProcFailedToRunError(#[source] IoError),
    #[error("failed to spawn subprocess")]
    ProcFailedToSpawnError(#[source] IoError),
    #[error("string contains null byte")]
    ProcNullByteError,
    #[error("failed join command to quoted string")]
    ProcQuoteError(#[source] QuoteError),
    #[error("failed to attach to stream of subprocess")]
    ProcStreamAttachError,
    #[error("failed decode stream into valid utf8")]
    ProcStreamDecodingError(#[source] Utf8Error),
    #[error("failed to read from stream of subprocess")]
    ProcStreamReadError(#[source] IoError),
}
