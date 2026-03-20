use thiserror::Error as ThisError;

use crate::engine::EngineError;
use crate::sys::SysError;
use crate::traits::Traverse;

pub enum Exit {
    ExitOk = 0,
    ExitWithError = 1,
}

#[derive(ThisError, Debug)]
pub enum CliError {
    #[error("sys subsystem error")]
    SysError(#[source] SysError),
    #[error("engine subsystem error")]
    EngineError(#[source] EngineError),
}

impl Traverse for CliError {}
