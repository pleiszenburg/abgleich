use std::process::ExitCode;

use tracing::error;

use crate::traits::Traverse;

use super::dispatch::dispatch;
use super::errors::Exit;

pub fn entrypoint() -> ExitCode {
    match dispatch() {
        Ok(()) => ExitCode::from(Exit::ExitOk as u8),
        Err(err) => {
            error!(traceback = err.traverse());
            ExitCode::from(Exit::ExitWithError as u8)
        }
    }
}
