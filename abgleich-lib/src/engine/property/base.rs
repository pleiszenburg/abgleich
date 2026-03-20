use super::value::PropertyValue;

pub trait Base {
    fn get_value_ref(&self) -> &PropertyValue;

    fn set_value(&mut self, value: PropertyValue);
}
