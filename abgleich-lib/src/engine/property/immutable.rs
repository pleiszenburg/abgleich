use super::base::Base;
use super::value::PropertyValue;

pub struct Immutable {
    value: PropertyValue,
}

impl Immutable {
    pub const fn new(value: PropertyValue) -> Self {
        Self { value }
    }
}

impl Base for Immutable {
    fn get_value_ref(&self) -> &PropertyValue {
        &self.value
    }

    fn set_value(&mut self, value: PropertyValue) {
        self.value = value;
    }
}
