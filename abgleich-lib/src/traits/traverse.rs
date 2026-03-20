use std::error::Error;

use crate::consts::TRACEBACK_SEP;

pub trait Traverse
where
    Self: Sized + Error,
{
    fn traverse(&self) -> String {
        Self::recurse(&self)
    }

    fn recurse(error: &dyn Error) -> String {
        let msg = format!("{error}");
        let src = match error.source() {
            Some(source_error) => Self::recurse(source_error),
            _ => return msg,
        };
        format!("{msg}{TRACEBACK_SEP}{src}")
    }
}
