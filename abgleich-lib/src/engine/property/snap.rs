use std::str::FromStr;
use std::string::ToString;

use super::super::errors::EngineError;

#[derive(Clone, PartialEq, Eq)]
pub enum Snap {
    Always,
    Never,
    Changed,
}

impl Snap {
    pub fn to_char(&self) -> String {
        match self {
            Self::Always => "a".to_string(),
            Self::Changed => "c".to_string(),
            Self::Never => "n".to_string(),
        }
    }
}

impl FromStr for Snap {
    type Err = EngineError;

    fn from_str(raw: &str) -> Result<Self, EngineError> {
        match raw {
            "always" => Ok(Self::Always),
            "never" => Ok(Self::Never),
            "changed" => Ok(Self::Changed),
            _ => Err(EngineError::SnapPropertyUnknownError),
        }
    }
}

#[allow(clippy::to_string_trait_impl)]
impl ToString for Snap {
    fn to_string(&self) -> String {
        match self {
            Self::Always => "always".to_string(),
            Self::Changed => "changed".to_string(),
            Self::Never => "never".to_string(),
        }
    }
}
