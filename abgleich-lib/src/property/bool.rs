use std::str::FromStr;
use std::string::ToString;

use super::error::ValueError;
use super::raw::RawProperty;
use super::value::BaseValue;

pub enum BoolValue {
    On,
    Off,
}

impl From<&BoolValue> for bool {
    fn from(value: &BoolValue) -> Self {
        match value {
            BoolValue::On => true,
            BoolValue::Off => false,
        }
    }
}

impl BaseValue for BoolValue {
    fn from_raw(raw: &RawProperty) -> Result<Self, ValueError> {
        Self::from_str(&raw.value)
    }
}

impl FromStr for BoolValue {
    type Err = ValueError;

    fn from_str(raw: &str) -> Result<Self, ValueError> {
        match raw.to_lowercase().as_str() {
            "on" | "yes" => Ok(Self::On),
            "off" | "no" => Ok(Self::Off),
            _ => Err(ValueError::Bool {
                value: raw.to_string(),
            }),
        }
    }
}

#[allow(clippy::to_string_trait_impl)]
impl ToString for BoolValue {
    fn to_string(&self) -> String {
        match self {
            Self::On => "on".to_string(),
            Self::Off => "off".to_string(),
        }
    }
}
