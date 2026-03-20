use super::super::errors::EngineError;

#[derive(Debug)]
pub enum Origin {
    Inherited(String),
    Local,
    Default,
}

impl Origin {
    pub fn from_raw(raw: &str) -> Result<Self, EngineError> {
        if raw == "local" {
            return Ok(Self::Local);
        }
        if raw == "default" {
            return Ok(Self::Default);
        }
        if let Some(clean_raw) = raw.strip_prefix("inherited from") {
            return Ok(Self::Inherited(clean_raw.to_string()));
        }
        Err(EngineError::PropertyParseOriginError)
    }
}
