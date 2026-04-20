use std::str::FromStr;
use std::string::ToString;

use super::error::ValueError;
use super::raw::RawProperty;
use super::value::BaseValue;

#[derive(Clone, PartialEq, Eq)]
pub struct StringValue {
    value: String,
}

impl StringValue {
    #[must_use]
    pub fn unpack(&self) -> &str {
        &self.value
    }
}

impl BaseValue for StringValue {
    fn from_raw(raw: &RawProperty) -> Result<Self, ValueError> {
        Self::from_str(&raw.value)
    }
}

impl FromStr for StringValue {
    type Err = ValueError;

    fn from_str(raw: &str) -> Result<Self, ValueError> {
        Ok(Self {
            value: raw.to_string(),
        })
    }
}

#[allow(clippy::to_string_trait_impl)]
impl ToString for StringValue {
    fn to_string(&self) -> String {
        self.value.clone() // placeholder, currently unused
    }
}
