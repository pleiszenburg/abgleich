use std::str::FromStr;
use std::string::ToString;

use super::error::ValueError;
use super::raw::RawProperty;
use super::value::BaseValue;

#[derive(Clone, PartialEq, Eq)]
pub struct OptionalUIntValue {
    value: Option<u64>,
}

impl OptionalUIntValue {
    #[must_use]
    pub const fn unpack(&self) -> Option<&u64> {
        self.value.as_ref()
    }
}

impl BaseValue for OptionalUIntValue {
    fn from_raw(raw: &RawProperty) -> Result<Self, ValueError> {
        Self::from_str(&raw.value)
    }
}

impl FromStr for OptionalUIntValue {
    type Err = ValueError;

    fn from_str(raw: &str) -> Result<Self, ValueError> {
        Ok(Self{value: if raw == "none" {
            None
        } else {Some(raw
            .parse::<u64>()
            .map_err(|e| ValueError::UInt { value: raw.to_string(), source: e })?)
        }})
    }
}

#[allow(clippy::to_string_trait_impl)]
impl ToString for OptionalUIntValue {
    fn to_string(&self) -> String {
        self.value.as_ref().map_or_else(
            || "none".to_string(),
            |value| format!("{value}")
        )
    } // placeholder, currently unused
}
