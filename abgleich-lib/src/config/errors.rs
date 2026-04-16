use std::io::Error as IoError;
use std::string::FromUtf8Error;

use serde_yaml_ng::Error as YamlDeserializingError;
use thiserror::Error as ThisError;

#[derive(ThisError, Debug)]
pub enum ConfigError {
    #[error("no configuration file found")]
    ConfigNotFound,
    #[error("--direct and --insecure cannot be used together")]
    DirectAndInsecureConflict,
    #[error("i/o error, while {action}: {path}")]
    Io{
        action: String,
        path: String,
        source: IoError,
    },
    #[error("{msg}")]
    RouteParser {msg: String},
    #[error("{msg}")]
    RootParser {msg: String},
    #[error("utf8 decoding error: {path}")]
    Utf8Decoding{
        path: String,
        source: FromUtf8Error,
    },
    #[error("deserializing yaml failed: {path}")]
    YamlDeserializing{
        path: String,
        source: YamlDeserializingError,
    },
}
