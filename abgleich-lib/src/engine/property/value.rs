use super::snap::Snap;
use super::type_::Type;
use super::types::{PropertyInt, PropertyUInt, PropetyFloat};

pub enum PropertyValue {
    Type(Option<Type>),
    Bool(Option<bool>),
    Float(Option<PropetyFloat>),
    Int(Option<PropertyInt>),
    Snap(Option<Snap>),
    String(Option<String>),
    UInt(Option<PropertyUInt>),
}
