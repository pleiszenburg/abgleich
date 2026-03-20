use inquire::InquireError;
use thiserror::Error as ThisError;

use crate::subprocess::SubprocessError;

#[derive(ThisError, Debug)]
pub enum TransactionError {
    #[error("--direct cannot be used with route '{0}': consecutive duplicate hosts would cause a host to SSH to itself after route rewriting")]
    DirectConsecutiveDuplicateHostsError(String),
    #[error("transaction failed")]
    FailedError,
    #[error("inquire subsystem error")]
    InquireError(#[source] InquireError),
    #[error("{0} transaction(s) failed")]
    SomeTransactionsFailed(usize),
    #[error("subprocess subsystem error")]
    SubprocessError(#[source] SubprocessError),
}
