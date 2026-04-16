use crate::consts::{DEFAULT_FULLFORCE, VAR_FULLFORCE};
use crate::sys::envvar2bool;

use super::errors::TransactionBuildError;

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Force {
    No,
    Normal,
    Full,
}

impl Force {
    pub fn from_bool(force: bool) -> Result<Self, TransactionBuildError> {
        if !force {
            return Ok(Self::No);
        }
        let full = envvar2bool(VAR_FULLFORCE)
            .map_err(|e| TransactionBuildError::EnvironmentVariable {
                name: VAR_FULLFORCE.to_string(), source: e
            })?
            .unwrap_or(DEFAULT_FULLFORCE);
        if !full {
            return Ok(Self::Normal);
        }
        Ok(Self::Full)
    }
}
