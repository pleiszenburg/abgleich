use super::error::PropertyError;
use super::origin::Origin;
use super::raw::RawProperty;
use super::value::BaseValue;

pub trait BaseProperty<T: BaseValue>
where
    Self: Sized,
{
    fn get_value_ref(&self) -> &T;

    fn from_raw(raw: &RawProperty) -> Result<Self, PropertyError>;
}

pub struct ImmutableProperty<T: BaseValue> {
    value: T,
}

impl<T: BaseValue> BaseProperty<T> for ImmutableProperty<T> {
    fn from_raw(raw: &RawProperty) -> Result<Self, PropertyError> {
        Ok(Self {
            value: T::from_raw(raw).map_err(|e| PropertyError::Value {
                name: raw.name.clone(),
                source: e,
            })?,
        })
    }

    fn get_value_ref(&self) -> &T {
        &self.value
    }
}

pub struct MutableProperty<T: BaseValue> {
    value: T,
    #[allow(unused)]
    origin: Origin,
}

impl<T: BaseValue> MutableProperty<T> {
    #[allow(unused)]
    const fn get_origin_ref(&self) -> &Origin {
        &self.origin
    }
}

impl<T: BaseValue> BaseProperty<T> for MutableProperty<T> {
    fn from_raw(raw: &RawProperty) -> Result<Self, PropertyError> {
        Ok(Self {
            value: T::from_raw(raw).map_err(|e| PropertyError::Value {
                name: raw.name.clone(),
                source: e,
            })?,
            origin: Origin::from_raw(raw).map_err(|e| PropertyError::Value {
                name: raw.name.clone(),
                source: e,
            })?,
        })
    }

    fn get_value_ref(&self) -> &T {
        &self.value
    }
}
