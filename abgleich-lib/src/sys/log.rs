use tracing::Level;

use crate::consts::{DEFAULT_LOGLEVEL, VAR_LOGLEVEL};

use super::env::envvar2type_or;
use super::errors::SysError;

const fn translate_loglevel(level: u8) -> Level {
    #[allow(clippy::match_same_arms)]
    match level {
        0..10 => Level::TRACE,
        10..20 => Level::DEBUG,
        20..30 => Level::INFO,
        30..40 => Level::WARN,
        40..50 => Level::ERROR,
        _ => Level::TRACE,
    }
}

pub fn get_loglevel() -> Result<Level, SysError> {
    let level: u8 = envvar2type_or(VAR_LOGLEVEL, &DEFAULT_LOGLEVEL)?;
    Ok(translate_loglevel(level))
}
