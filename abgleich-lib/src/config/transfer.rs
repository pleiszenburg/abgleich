use super::errors::ConfigError;


#[derive(Clone, Debug, Default, Eq, PartialEq)]
pub struct InsecureHost {
    pub hostname: String,
    pub port: u16,
}


#[derive(Clone, Debug, Default)]
pub struct TransferOptions {
    pub compress: Option<u8>,
    pub direct: bool,
    pub insecure: Option<InsecureHost>,
    pub rate_limit: Option<u64>,
}


impl TransferOptions {
    #[must_use]
    pub const fn new() -> Self {
        Self {
            compress: None,
            direct: false,
            insecure: None,
            rate_limit: None,
        }
    }

    #[must_use]
    pub const fn with_compress(mut self, value: Option<u8>) -> Self {
        self.compress = value;
        self
    }

    pub fn with_direct(mut self, value: bool) -> Result<Self, ConfigError> {
        if value && self.insecure.is_some() {
            return Err(ConfigError::DirectAndInsecureConflict);
        }
        self.direct = value;
        Ok(self)
    }

    pub fn with_insecure(mut self, value: Option<InsecureHost>) -> Result<Self, ConfigError> {
        if self.direct && value.is_some() {
            return Err(ConfigError::DirectAndInsecureConflict);
        }
        self.insecure = value;
        Ok(self)
    }

    #[must_use]
    pub const fn with_rate_limit(mut self, value: Option<u64>) -> Self {
        self.rate_limit = value;
        self
    }
}
