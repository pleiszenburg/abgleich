use std::num::TryFromIntError;

use thiserror::Error as ThisError;

use crate::config::ConfigError;
use crate::property::{PropertyError, ValueError};
use crate::sys::SysError;
#[cfg(feature = "cli")]
use crate::transaction::TransactionCliError;
use crate::transaction::{TransactionBuildError, TransactionRunError};

#[derive(ThisError, Debug)]
pub enum EngineError {
    #[error("usize exceeds value than can be handled on less than 64 bit arch: {value}")]
    ArchUsize{
        value: i64,
        source: TryFromIntError,
    },
    #[error("command {command} not found on {host} for user {user}")]
    CommandNotFound {
        host: String,
        user: String,
        command: String,
    },
    #[error("config subsystem error")]
    Config(#[source] ConfigError),
    #[error("type of dataset '{name}' in '{root}' is unknown")]
    DatasetTypeUnknown{
        root: String,
        name: String,
    },
    #[error("dataset '{name}' in '{root}' is unknown")]
    DatasetUnknown{
        root: String,
        name: String,
    },
    #[error("dataset {dataset} does not have snapshots and can not be transferred")]
    DatasetWithoutSnapshot { dataset: String },
    #[error("failed to load value from environment variable '{name}'")]
    EnvironmentVariable{
        name: String,
        source: SysError,
    },
    #[error("property subsystem error")]
    Property(#[source] PropertyError),
    #[error("unknown mount status of dataset '{name}' in '{root}'")]
    UnknownMounted{
        root: String,
        name: String,
    },
    #[error("unknown number of written bytes for dataset '{name}' in '{root}'")]
    UnknownWritten{
        root: String,
        name: String,
    },
    #[error("snapshot sequence comparison failed for source '{src}' and target '{tgt}' datasets: {msg}")]
    Sequence {
        msg: String,
        src: String,
        tgt: String,
    },
    #[error("transaction build subsystem error")]
    TransactionBuild(#[source] TransactionBuildError),
    #[cfg(feature = "cli")]
    #[error("transaction cli subsystem error")]
    TransactionCli(#[source] TransactionCliError),
    #[error("transaction run subsystem error")]
    TransactionRun(#[source] TransactionRunError),
    #[error("failed to parse property '{name}'")]
    Value {
        name: String,
        source: ValueError,
    },
}
