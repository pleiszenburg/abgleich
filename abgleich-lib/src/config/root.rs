use std::str::FromStr;
use std::string::ToString;

use super::errors::ConfigError;

pub struct Root {
    value: String,
}

impl Root {
    pub fn new(value: String) -> Result<Self, ConfigError> {
        Self::assert_valid(&value)?;
        Ok(Self { value })
    }

    #[must_use]
    pub fn as_clean_str(&self) -> &str {
        if self.value.ends_with('/') {
            &self.value[..self.value.len() - 1]
        } else {
            &self.value
        }
    }

    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.value
    }

    fn assert_valid(value: &str) -> Result<(), ConfigError> {
        if value.is_empty() {
            return Err(ConfigError::LocationRootEmptyError);
        }
        if value.chars().nth(0).unwrap() == '/' {
            return Err(ConfigError::LocationRootLeadingSlashError);
        }
        Ok(())
    }

    #[must_use]
    pub fn to_clean_string(&self) -> String {
        self.as_clean_str().to_string()
    }
}

impl FromStr for Root {
    type Err = ConfigError;

    fn from_str(value: &str) -> Result<Self, ConfigError> {
        Self::new(value.to_string())
    }
}

#[allow(clippy::to_string_trait_impl)]
impl ToString for Root {
    fn to_string(&self) -> String {
        self.value.clone()
    }
}

impl Clone for Root {
    fn clone(&self) -> Self {
        Self {
            value: self.value.clone(),
        }
    }
}

impl PartialEq for Root {
    fn eq(&self, other: &Self) -> bool {
        self.value == *other.as_str()
    }
}
