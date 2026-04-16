use tracing::{debug, Value};

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
            let value = value.to_lowercase();
            if value == "1" || value == "true" || value == "yes" {
                debug!(
                    msg = "environment variable parsed",
                    name = name,
                    value = true,
                    dtype = "env-var"
                );
                return Ok(Some(true));
            }
            if value == "0" || value == "false" || value == "no" {
                debug!(
                    msg = "environment variable parsed",
                    name = name,
                    value = false,
                    dtype = "env-var"
                );
                return Ok(Some(false));
            }
            Err(SysError::BoolParser(value))
        }
        Err(_) => Ok(None),
    }
}

pub fn envvar2bool_or(name: &str, default: bool) -> Result<bool, SysError> {
    Ok(envvar2bool(name)?.map_or(default, |result| result))
}

pub fn envvar2type<T: FromStr + Value>(name: &str) -> Result<Option<T>, SysError> {
    match env::var(name) {
        Ok(value) => {
            debug!(
                msg = "environment variable detected",
                name = name,
                value = value,
                dtype = "env-var"
            );
            let value: T = value
                .parse::<T>()
                .map_err(|_| SysError::GenericParser(value))?;
            debug!(
                msg = "environment variable parsed",
                name = name,
                value = value,
                dtype = "env-var"
            );
            Ok(Some(value))
        }
        Err(_) => Ok(None),
    }
}

pub fn envvar2type_or<T: FromStr + Value + Clone>(name: &str, default: &T) -> Result<T, SysError> {
    envvar2type(name)?.map_or_else(|| Ok(default.clone()), |result| Ok(result))
}
