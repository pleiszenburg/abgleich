use std::num::{ParseFloatError, ParseIntError, TryFromIntError};

use thiserror::Error as ThisError;

use crate::config::ConfigError;
use crate::sys::SysError;
use crate::transaction::TransactionError;

#[derive(ThisError, Debug)]
pub enum EngineError {
    #[error("usize exceeds value than can be handled on 32 bit arch")]
    ArchUsizeError(#[source] TryFromIntError),
    #[error("config subsystem error")]
    ConfigError(#[source] ConfigError),
    #[error("type of dataset is unknown")]
    DatasetTypeUnknownError,
    #[error("dataset is unknown")]
    DatasetUnknownError,
    #[error("target contains snapshot after last common snapshot")]
    DatasetSnapshotAfterLastCommonError,
    #[error("creation times of identical snapshot do not match")]
    DatasetSnapshotCreationMismatchError,
    #[error("creation time of sequence of snapshots does not monotonically increase")]
    DatasetSnapshotCreationNotMonotonicError,
    #[error("datasets do not contain common snapshot")]
    DatasetSnapshotNoCommonError,
    #[error("failed to validate sequence of snapshots between two datasets")]
    DatasetSnapshotSequenceValidationError,
    #[error("dataset {dataset} does not have snapshots and can not be transferred")]
    DatasetWithoutSnapshotError { dataset: String },
    #[error("the configured overlap is set to zero")]
    OverlapZeroError,
    #[error("property is not mutable")]
    PropertyNotMutableError,
    #[error("failed to parse origin of property")]
    PropertyParseOriginError,
    #[error("failed to parse bool property")]
    PropertyParseBoolError,
    #[error("failed to parse float property")]
    PropertyParseFloatError(#[source] ParseFloatError),
    #[error("insufficient number of fragments for a property")]
    PropertyParseFragmentsError,
    #[error("failed to parse int property")]
    PropertyParseIntError(#[source] ParseIntError),
    #[error("failed to access property value due to wrong type")]
    PropertyTypeError,
    #[error("failed to parse unsigned int property: {name}")]
    PropertyParseUIntError { name: String },
    #[error("property name is unknown")]
    PropertyUnknownError,
    #[error("snap property set to unknown value")]
    SnapPropertyUnknownError,
    #[error("sys subsystem error")]
    SysError(#[source] SysError),
    #[error("transaction subsystem error")]
    TransactionError(#[source] TransactionError),
    #[error("the type of dataset can not be identified")]
    TypeUnknownError,
    #[error("zfs command not found on {host}")]
    ZfsCommandNotFound { host: String },
    #[error("zpool command not found")]
    ZpoolCommandNotFound,
    #[error("nc command not found on {host}")]
    NcCommandNotFound { host: String },
    #[error("pv command not found on {host}")]
    PvCommandNotFound { host: String },
    #[error("xz command not found on {host}")]
    XzCommandNotFound { host: String },
    #[error("--direct and --insecure cannot be used together")]
    DirectAndInsecureConflict,
}
