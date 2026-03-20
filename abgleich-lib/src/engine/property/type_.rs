use std::str::FromStr;
use std::string::ToString;

use super::super::errors::EngineError;

#[derive(Clone, PartialEq, Eq)]
pub enum Type {
    Filesystem,
    Volume,
    Snapshot,
}

impl Type {
    pub fn to_char(&self) -> String {
        match self {
            Self::Filesystem => "f".to_string(),
            Self::Snapshot => "s".to_string(),
            Self::Volume => "v".to_string(),
        }
    }
}

impl FromStr for Type {
    type Err = EngineError;

    fn from_str(raw: &str) -> Result<Self, EngineError> {
        match raw {
            "filesystem" => Ok(Self::Filesystem),
            "volume" => Ok(Self::Volume),
            "snapshot" => Ok(Self::Snapshot),
            _ => Err(EngineError::TypeUnknownError),
        }
    }
}

#[allow(clippy::to_string_trait_impl)]
impl ToString for Type {
    fn to_string(&self) -> String {
        match self {
            Self::Filesystem => "filesystem".to_string(),
            Self::Snapshot => "snapshot".to_string(),
            Self::Volume => "volume".to_string(),
        }
    }
}
