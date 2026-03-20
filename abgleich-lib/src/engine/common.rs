use super::meta::Meta;
use super::property::Type;

pub trait Common {
    fn get_meta_ref(&self) -> &Meta;

    fn get_creation(&self) -> i64 {
        self.get_meta_ref().creation.get_int().unwrap().unwrap()
    }

    fn get_compressratio(&self) -> f32 {
        self.get_meta_ref()
            .compressratio
            .get_float()
            .unwrap()
            .unwrap() // safe operation
    }

    fn get_name_ref(&self) -> &str {
        &self.get_meta_ref().name
    }

    fn get_referenced(&self) -> u64 {
        self.get_meta_ref().referenced.get_uint().unwrap().unwrap() // safe operation
    }

    fn get_type(&self) -> Type {
        self.get_meta_ref().type_.get_type().unwrap().unwrap() // safe operation
    }

    fn get_used(&self) -> u64 {
        self.get_meta_ref().used.get_uint().unwrap().unwrap() // safe operation
    }
}
