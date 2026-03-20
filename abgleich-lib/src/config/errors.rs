use std::io::Error as IoError;
use std::string::FromUtf8Error;

use serde_yaml_ng::Error as YamlDeserializingError;
use thiserror::Error as ThisError;

#[derive(ThisError, Debug)]
pub enum ConfigError {
    #[error("no configuration file found")]
    ConfigNotFoundError,
    #[error("i/o error")]
    IoError(#[source] IoError),
    #[error("location description does not have exactly one (root) or two fragments (route:root)")]
    LocationFragmentsError,
    #[error("localhost in unexpected position in location route fragment")]
    LocationLocalhostPositionError,
    #[error("location root fragment is empty")]
    LocationRootEmptyError,
    #[error("location root fragment must not begin with a slash")]
    LocationRootLeadingSlashError,
    #[error("optional location user fragment provided but empty")]
    LocationUserEmptyError,
    #[error("utf8 decoding error")]
    Utf8DecodingError(#[source] FromUtf8Error),
    #[error("deserializing yaml failed")]
    YamlDeserializingError(#[source] YamlDeserializingError),
}
