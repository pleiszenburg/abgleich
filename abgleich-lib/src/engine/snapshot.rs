use super::common::Common;
use super::meta::Meta;

pub struct Snapshot {
    meta: Meta,
}

impl Snapshot {
    pub const fn new(meta: Meta) -> Self {
        Self { meta }
    }
}

impl Common for Snapshot {
    fn get_meta_ref(&self) -> &Meta {
        &self.meta
    }
}
