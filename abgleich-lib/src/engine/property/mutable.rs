use super::base::Base;
use super::origin::Origin;
use super::value::PropertyValue;

pub struct Mutable {
    value: PropertyValue,
    origin: Option<Origin>,
}

impl Mutable {
    pub const fn new(value: PropertyValue) -> Self {
        Self {
            value,
            origin: None,
        }
    }

    pub const fn get_origin_ref(&self) -> Option<&Origin> {
        match &self.origin {
            Some(origin) => Some(origin),
            _ => None,
        }
    }

    pub fn set_origin(&mut self, origin: Option<Origin>) {
        self.origin = origin;
    }
}

impl Base for Mutable {
    fn get_value_ref(&self) -> &PropertyValue {
        &self.value
    }

    fn set_value(&mut self, value: PropertyValue) {
        self.value = value;
    }
}
