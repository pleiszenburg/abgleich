use std::str::FromStr;

use super::super::errors::EngineError;

use super::base::Base;
use super::immutable::Immutable;
use super::mutable::Mutable;
use super::origin::Origin;
use super::parser::parse_bool;
use super::raw::RawProperty;
use super::snap::Snap;
use super::type_::Type;
use super::types::{PropertyInt, PropertyUInt, PropetyFloat};
use super::value::PropertyValue;

pub enum Property {
    Mutable(Mutable),
    Immutable(Immutable),
}

impl Property {
    #[must_use]
    pub const fn is_mutable(&self) -> bool {
        match self {
            Self::Mutable(_) => true,
            Self::Immutable(_) => false,
        }
    }

    const fn new_empty(mutable: bool, value: PropertyValue) -> Self {
        if mutable {
            Self::Mutable(Mutable::new(value))
        } else {
            Self::Immutable(Immutable::new(value))
        }
    }

    #[must_use]
    pub const fn empty_bool(mutable: bool) -> Self {
        Self::new_empty(mutable, PropertyValue::Bool(None))
    }

    #[must_use]
    pub const fn empty_float(mutable: bool) -> Self {
        Self::new_empty(mutable, PropertyValue::Float(None))
    }

    #[must_use]
    pub const fn empty_int(mutable: bool) -> Self {
        Self::new_empty(mutable, PropertyValue::Int(None))
    }

    #[must_use]
    pub const fn empty_snap(mutable: bool) -> Self {
        Self::new_empty(mutable, PropertyValue::Snap(None))
    }

    #[must_use]
    pub const fn empty_string(mutable: bool) -> Self {
        Self::new_empty(mutable, PropertyValue::String(None))
    }

    #[must_use]
    pub const fn empty_type(mutable: bool) -> Self {
        Self::new_empty(mutable, PropertyValue::Type(None))
    }

    #[must_use]
    pub const fn empty_uint(mutable: bool) -> Self {
        Self::new_empty(mutable, PropertyValue::UInt(None))
    }

    fn get_value_ref(&self) -> &PropertyValue {
        match self {
            Self::Immutable(property) => property.get_value_ref(),
            Self::Mutable(property) => property.get_value_ref(),
        }
    }

    pub fn get_bool(&self) -> Result<Option<bool>, EngineError> {
        match *self.get_value_ref() {
            PropertyValue::Bool(value) => Ok(value),
            _ => Err(EngineError::PropertyTypeError),
        }
    }

    pub fn get_float(&self) -> Result<Option<PropetyFloat>, EngineError> {
        match *self.get_value_ref() {
            PropertyValue::Float(value) => Ok(value),
            _ => Err(EngineError::PropertyTypeError),
        }
    }

    pub fn get_int(&self) -> Result<Option<PropertyInt>, EngineError> {
        match *self.get_value_ref() {
            PropertyValue::Int(value) => Ok(value),
            _ => Err(EngineError::PropertyTypeError),
        }
    }

    pub fn get_snap(&self) -> Result<Option<Snap>, EngineError> {
        match self.get_value_ref() {
            PropertyValue::Snap(value) => Ok(value.clone()),
            _ => Err(EngineError::PropertyTypeError),
        }
    }

    pub fn get_string_ref(&self) -> Result<Option<&str>, EngineError> {
        match self.get_value_ref() {
            PropertyValue::String(value) => Ok(value.as_deref()),
            _ => Err(EngineError::PropertyTypeError),
        }
    }

    pub fn get_type(&self) -> Result<Option<Type>, EngineError> {
        match self.get_value_ref() {
            PropertyValue::Type(value) => Ok(value.clone()),
            _ => Err(EngineError::PropertyTypeError),
        }
    }

    pub const fn get_origin_ref(&self) -> Result<Option<&Origin>, EngineError> {
        match self {
            Self::Mutable(property) => Ok(property.get_origin_ref()),
            Self::Immutable(_) => Err(EngineError::PropertyNotMutableError),
        }
    }

    pub fn get_uint(&self) -> Result<Option<PropertyUInt>, EngineError> {
        match *self.get_value_ref() {
            PropertyValue::UInt(value) => Ok(value),
            _ => Err(EngineError::PropertyTypeError),
        }
    }

    pub fn set_raw(&mut self, raw: &RawProperty) -> Result<(), EngineError> {
        let old_value = self.get_value_ref();
        let new_value = Self::parse_raw(raw, old_value)?;
        match self {
            Self::Immutable(property) => property.set_value(new_value),
            Self::Mutable(property) => {
                property.set_value(new_value);
                property.set_origin(Some(Origin::from_raw(&raw.meta)?));
            }
        }
        Ok(())
    }

    fn parse_raw(raw: &RawProperty, value: &PropertyValue) -> Result<PropertyValue, EngineError> {
        Ok(match value {
            PropertyValue::Type(_) => PropertyValue::Type(Some(Type::from_str(&raw.value)?)),
            PropertyValue::Bool(_) => PropertyValue::Bool(Some(parse_bool(&raw.value)?)),
            PropertyValue::Float(_) => PropertyValue::Float(Some(
                raw.value
                    .parse::<PropetyFloat>()
                    .map_err(EngineError::PropertyParseFloatError)?,
            )),
            PropertyValue::Int(_) => PropertyValue::Int(Some(
                raw.value
                    .parse::<PropertyInt>()
                    .map_err(EngineError::PropertyParseIntError)?,
            )),
            PropertyValue::Snap(_) => PropertyValue::Snap(Some(Snap::from_str(&raw.value)?)),
            PropertyValue::String(_) => PropertyValue::String(Some(raw.value.clone())),
            PropertyValue::UInt(_) => PropertyValue::UInt({
                if raw.value == "none" {
                    None
                } else {
                    match raw.value.parse::<PropertyUInt>() {
                        Ok(value) => Some(value),
                        Err(_) => {
                            return Err(EngineError::PropertyParseUIntError {
                                name: raw.name.clone(),
                            });
                        }
                    }
                }
            }),
        })
    }
}
