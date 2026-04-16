use thiserror::Error as ThisError;

use crate::config::ConfigError;
use crate::engine::EngineError;
use crate::sys::SysError;
use crate::traits::Traverse;

pub enum Exit {
    ExitOk = 0,
    ExitWithError = 1,
}

#[derive(ThisError, Debug)]
#[allow(clippy::enum_variant_names)]
pub enum CliError {
    #[error("config subsystem error")]
    Config(#[source] ConfigError),
    #[error("sys subsystem error")]
    Sys(#[source] SysError),
    #[error("engine subsystem error")]
    Engine(#[source] EngineError),
}

impl Traverse for CliError {}
