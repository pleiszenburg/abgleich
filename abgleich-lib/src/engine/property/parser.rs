use super::super::errors::EngineError;

pub fn parse_bool(raw: &str) -> Result<bool, EngineError> {
    match raw.to_lowercase().as_str() {
        "on" | "yes" => Ok(true),
        "off" | "no" => Ok(false),
        _ => Err(EngineError::PropertyParseBoolError),
    }
}
