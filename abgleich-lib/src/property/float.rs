use std::str::FromStr;
use std::string::ToString;

use super::error::ValueError;
use super::raw::RawProperty;
use super::value::BaseValue;

#[derive(Clone, PartialEq)]
pub struct FloatValue {
    value: f32,
}

impl FloatValue {
    #[must_use]
    pub const fn unpack(&self) -> &f32 {
        &self.value
    }
}

impl BaseValue for FloatValue {
    fn from_raw(raw: &RawProperty) -> Result<Self, ValueError> {
        Self::from_str(&raw.value)
    }
}

impl FromStr for FloatValue {
    type Err = ValueError;

    fn from_str(raw: &str) -> Result<Self, ValueError> {
        Ok(Self{value: raw
            .parse::<f32>()
            .map_err(|e| ValueError::Float { value: raw.to_string(), source: e })?
        })
    }
}

#[allow(clippy::to_string_trait_impl)]
impl ToString for FloatValue {
    fn to_string(&self) -> String {
        format!("{}", self.value) // placeholder, currently unused
    }
}
