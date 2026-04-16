use super::error::ValueError;
use super::raw::RawProperty;

pub trait BaseValue where Self: Sized {
    fn from_raw(raw: &RawProperty) -> Result<Self, ValueError>;
}
