use std::str::FromStr;
use std::string::ToString;

use super::error::ValueError;
use super::raw::RawProperty;
use super::value::BaseValue;

#[derive(Clone, PartialEq, Eq)]
pub enum SnapValue {
    Always,
    Never,
    Changed,
}

impl BaseValue for SnapValue {
    fn from_raw(raw: &RawProperty) -> Result<Self, ValueError> {
        Self::from_str(&raw.value)
    }
}

impl SnapValue {
    #[must_use]
    pub fn to_char(&self) -> String {
        match self {
            Self::Always => "a".to_string(),
            Self::Changed => "c".to_string(),
            Self::Never => "n".to_string(),
        }
    }
}

impl FromStr for SnapValue {
    type Err = ValueError;

    fn from_str(raw: &str) -> Result<Self, ValueError> {
        match raw {
            "always" => Ok(Self::Always),
            "never" => Ok(Self::Never),
            "changed" => Ok(Self::Changed),
            _ => Err(ValueError::Snap { value: raw.to_string() }),
        }
    }
}

#[allow(clippy::to_string_trait_impl)]
impl ToString for SnapValue {
    fn to_string(&self) -> String {
        match self {
            Self::Always => "always".to_string(),
            Self::Changed => "changed".to_string(),
            Self::Never => "never".to_string(),
        }
    }
}
