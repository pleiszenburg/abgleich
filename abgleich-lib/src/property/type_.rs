use std::str::FromStr;
use std::string::ToString;

use super::error::ValueError;
use super::raw::RawProperty;
use super::value::BaseValue;

#[derive(Clone, PartialEq, Eq)]
pub enum TypeValue {
    Filesystem,
    Volume,
    Snapshot,
}

impl BaseValue for TypeValue {
    fn from_raw(raw: &RawProperty) -> Result<Self, ValueError> {
        Self::from_str(&raw.value)
    }
}

impl TypeValue {
    #[must_use]
    pub fn to_char(&self) -> String {
        match self {
            Self::Filesystem => "f".to_string(),
            Self::Snapshot => "s".to_string(),
            Self::Volume => "v".to_string(),
        }
    }
}

impl FromStr for TypeValue {
    type Err = ValueError;

    fn from_str(raw: &str) -> Result<Self, ValueError> {
        match raw {
            "filesystem" => Ok(Self::Filesystem),
            "volume" => Ok(Self::Volume),
            "snapshot" => Ok(Self::Snapshot),
            _ => Err(ValueError::Type_ {
                value: raw.to_string(),
            }),
        }
    }
}

#[allow(clippy::to_string_trait_impl)]
impl ToString for TypeValue {
    fn to_string(&self) -> String {
        match self {
            Self::Filesystem => "filesystem".to_string(),
            Self::Snapshot => "snapshot".to_string(),
            Self::Volume => "volume".to_string(),
        }
    }
}
