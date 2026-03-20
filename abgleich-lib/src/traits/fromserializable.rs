use std::error::Error;

pub trait FromSerializable<A, E>
where
    Self: Sized,
    E: Error,
{
    fn from_serializable(serializable: A) -> Result<Self, E>;
}
