use std::str::FromStr;
use std::string::ToString;

use crate::consts::ROOT_DELIMITER;

use super::errors::ConfigError;

#[derive(Clone, PartialEq, Eq)]
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
        if self.value.ends_with(ROOT_DELIMITER) {
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
            return Err(ConfigError::RootParser { msg: "location root fragment is empty".to_string() });
        }
        if value.chars().nth(0).unwrap() == ROOT_DELIMITER {
            return Err(ConfigError::RootParser { msg: "location root fragment begins with a slash".to_string() });
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
