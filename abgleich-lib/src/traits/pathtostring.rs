use std::error::Error;
use std::ffi::OsStr;
use std::path::Path;

pub trait OsStrToString<E: Error> {
    fn to_string(&self, err: E) -> Result<String, E>;
}

impl<E: Error> OsStrToString<E> for OsStr {
    fn to_string(&self, err: E) -> Result<String, E> {
        self.to_os_string()
            .into_string()
            .map_or_else(|_| Err(err), |path| Ok(path))
    }
}

pub trait PathToString<E: Error> {
    fn to_string(&self, err: E) -> Result<String, E>;
}

impl<E: Error> PathToString<E> for Path {
    fn to_string(&self, err: E) -> Result<String, E> {
        self.as_os_str().to_string(err)
    }
}
