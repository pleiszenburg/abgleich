use thiserror::Error as ThisError;

#[derive(ThisError, Debug)]
#[non_exhaustive]
pub enum SysError {
    #[error("BoolParserError")]
    BoolParserError,
    #[error("ParseGenericError")]
    ParseGenericError,
}
