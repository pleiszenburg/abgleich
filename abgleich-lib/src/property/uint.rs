use std::str::FromStr;
use std::string::ToString;

use super::error::ValueError;
use super::raw::RawProperty;
use super::value::BaseValue;

#[derive(Clone, PartialEq, Eq)]
pub struct UIntValue {
    value: u64,
}

impl UIntValue {
    #[must_use]
    pub const fn unpack(&self) -> &u64 {
        &self.value
    }
}

impl BaseValue for UIntValue {
    fn from_raw(raw: &RawProperty) -> Result<Self, ValueError> {
        Self::from_str(&raw.value)
    }
}

impl FromStr for UIntValue {
    type Err = ValueError;

    fn from_str(raw: &str) -> Result<Self, ValueError> {
        Ok(Self {
            value: raw.parse::<u64>().map_err(|e| ValueError::UInt {
                value: raw.to_string(),
                source: e,
            })?,
        })
    }
}

#[allow(clippy::to_string_trait_impl)]
impl ToString for UIntValue {
    fn to_string(&self) -> String {
        format!("{}", self.value) // placeholder, currently unused
    }
}
