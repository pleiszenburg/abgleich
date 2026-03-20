use tracing::debug;

use std::env;
use std::str::FromStr;

use super::errors::SysError;

#[must_use]
pub fn envvar2string(name: &str) -> Option<String> {
    env::var(name).map_or(None, |value| {
        debug!(
            msg = "environment variable detected",
            name = name,
            value = value,
            dtype = "env-var"
        );
        Some(value)
    })
}

#[must_use]
pub fn envvar2string_or(name: &str, default: &str) -> String {
    envvar2string(name).unwrap_or_else(|| default.to_string())
}

pub fn envvar2bool(name: &str) -> Result<Option<bool>, SysError> {
    match env::var(name) {
        Ok(value) => {
            debug!(
                msg = "environment variable detected",
                name = name,
                value = value,
                dtype = "env-var"
            );
            let name = name.to_lowercase();
            if name == "1" || name == "true" || name == "yes" {
                return Ok(Some(true));
            }
            if name == "0" || name == "false" || name == "no" {
                return Ok(Some(false));
            }
            Err(SysError::BoolParserError)
        }
        Err(_) => Ok(None),
    }
}

pub fn envvar2bool_or(name: &str, default: bool) -> Result<bool, SysError> {
    Ok(envvar2bool(name)?.map_or(default, |result| result))
}

pub fn envvar2type<T: FromStr>(name: &str) -> Result<Option<T>, SysError> {
    match env::var(name) {
        Ok(value) => {
            debug!(
                msg = "environment variable detected",
                name = name,
                value = value,
                dtype = "env-var"
            );
            Ok(Some(
                value
                    .parse::<T>()
                    .map_err(|_| SysError::ParseGenericError)?,
            ))
        }
        Err(_) => Ok(None),
    }
}

pub fn envvar2type_or<T: FromStr + Clone>(name: &str, default: &T) -> Result<T, SysError> {
    envvar2type(name)?.map_or_else(|| Ok(default.clone()), |result| Ok(result))
}
