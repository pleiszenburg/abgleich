use std::str::FromStr;
use std::string::ToString;

use super::error::ValueError;
use super::raw::RawProperty;

#[derive(Debug)]
pub enum Origin {
    Inherited(String),
    Local,
    Default,
}

impl Origin {
    pub fn from_raw(raw: &RawProperty) -> Result<Self, ValueError> {
        Self::from_str(&raw.origin)
    }
}

impl FromStr for Origin {
    type Err = ValueError;

    fn from_str(raw: &str) -> Result<Self, ValueError> {
        if raw == "local" {
            return Ok(Self::Local);
        }
        if raw == "default" {
            return Ok(Self::Default);
        }
        if let Some(parent) = raw.strip_prefix("inherited from ") {
            return Ok(Self::Inherited(parent.to_string()));
        }
        Err(ValueError::Origin {
            value: raw.to_string(),
        })
    }
}

#[allow(clippy::to_string_trait_impl)]
impl ToString for Origin {
    fn to_string(&self) -> String {
        match self {
            Self::Inherited(parent) => format!("inherited from {parent}"),
            Self::Local => "local".to_string(),
            Self::Default => "default".to_string(),
        }
    }
}
