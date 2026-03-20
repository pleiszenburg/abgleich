use std::error::Error;

pub trait ToSerializable<A, E: Error> {
    fn to_serializable(&self) -> Result<A, E>;
}
