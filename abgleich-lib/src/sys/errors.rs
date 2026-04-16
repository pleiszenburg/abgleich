use thiserror::Error as ThisError;

#[derive(ThisError, Debug)]
#[non_exhaustive]
pub enum SysError {
    #[error("failed to parse value into boolean: {0}")]
    BoolParser(String),
    #[error("failed to parse value: {0}")]
    GenericParser(String),
}
