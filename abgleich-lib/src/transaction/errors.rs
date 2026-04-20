#[cfg(feature = "cli")]
use inquire::InquireError;
use thiserror::Error as ThisError;

use crate::subprocess::SubprocessError;
use crate::sys::SysError;
use crate::traits::Traverse;

#[derive(ThisError, Debug)]
pub enum TransactionBuildError {
    #[error(
        "--direct cannot be used with route '{0}': consecutive duplicate hosts would cause a host to SSH to itself after route rewriting"
    )]
    DirectConsecutiveDuplicateHosts(String),
    #[error("failed to load value from environment variable '{name}'")]
    EnvironmentVariable { name: String, source: SysError },
    #[error("subprocess subsystem error")]
    Subprocess(#[source] SubprocessError),
}

#[cfg(feature = "cli")]
#[derive(ThisError, Debug)]
pub enum TransactionCliError {
    #[error("inquire subsystem error")]
    Inquire(#[source] InquireError),
    #[error("transaction run subsystem error")]
    Run(#[source] TransactionRunError),
}

#[derive(ThisError, Debug)]
pub enum TransactionRunError {
    #[error("transaction failed, {reason}: {description}")]
    Failed { reason: String, description: String },
    #[error("{0} transaction(s) failed")]
    SomeFailed(usize),
    #[error("subprocess subsystem error")]
    Subprocess(#[source] SubprocessError),
}

impl Traverse for TransactionRunError {}
