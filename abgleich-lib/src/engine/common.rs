use crate::property::{BaseProperty, Description, TypeValue};

pub trait Common {
    fn get_description_ref(&self) -> &Description;

    fn get_creation(&self) -> i64 {
        *self.get_description_ref().creation.as_ref().unwrap().get_value_ref().unpack() // safe operation
    }

    fn get_compressratio(&self) -> f32 {
        *self.get_description_ref().compressratio.as_ref().unwrap().get_value_ref().unpack() // safe operation
    }

    fn get_name_ref(&self) -> &str {
        &self.get_description_ref().name
    }

    fn get_referenced(&self) -> u64 {
        *self.get_description_ref().referenced.as_ref().unwrap().get_value_ref().unpack() // safe operation
    }

    fn get_type(&self) -> TypeValue {
        self.get_description_ref().type_.as_ref().unwrap().get_value_ref().clone() // safe operation
    }

    fn get_used(&self) -> u64 {
        *self.get_description_ref().used.as_ref().unwrap().get_value_ref().unpack() // safe operation
    }
}
