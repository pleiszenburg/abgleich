use std::str::FromStr;
use std::string::ToString;

use super::error::ValueError;
use super::raw::RawProperty;
use super::value::BaseValue;

#[derive(Clone, PartialEq, Eq)]
pub struct IntValue {
    value: i64,
}

impl IntValue {
    #[must_use]
    pub const fn unpack(&self) -> &i64 {
        &self.value
    }
}

impl BaseValue for IntValue {
    fn from_raw(raw: &RawProperty) -> Result<Self, ValueError> {
        Self::from_str(&raw.value)
    }
}

impl FromStr for IntValue {
    type Err = ValueError;

    fn from_str(raw: &str) -> Result<Self, ValueError> {
        Ok(Self{value: raw
            .parse::<i64>()
            .map_err(|e| ValueError::Int { value: raw.to_string(), source: e })?
        })
    }
}

#[allow(clippy::to_string_trait_impl)]
impl ToString for IntValue {
    fn to_string(&self) -> String {
        format!("{}", self.value) // placeholder, currently unused
    }
}
