use std::num::{ParseFloatError, ParseIntError};

use thiserror::Error as ThisError;

#[derive(ThisError, Debug)]
pub enum PropertyError {
    #[error("at sign missing from presumed snapshot name in '{name}'")]
    MissingAt { name: String },
    #[error("insufficient number of tab-separated fragments for a property in line: '{line}'")]
    ParseFragments { line: String },
    #[error("failed to parse property '{name}'")]
    Value { name: String, source: ValueError },
}

#[derive(ThisError, Debug)]
pub enum ValueError {
    #[error("'{value}' into bool")]
    Bool { value: String },
    #[error("'{value}' into float")]
    Float {
        value: String,
        source: ParseFloatError,
    },
    #[error("'{value}' into int")]
    Int {
        value: String,
        source: ParseIntError,
    },
    #[error("'{value}' into origin")]
    Origin { value: String },
    #[error("'{value}' into snap")]
    Snap { value: String },
    #[error("'{value}' into type")]
    Type_ { value: String },
    #[error("'{value}' into uint")]
    UInt {
        value: String,
        source: ParseIntError,
    },
}
