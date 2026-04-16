use crate::property::Description;

use super::common::Common;

pub struct Snapshot {
    description: Description,
}

impl Snapshot {
    pub const fn from_description(description: Description) -> Self {
        Self { description }
    }
}

impl Common for Snapshot {
    fn get_description_ref(&self) -> &Description {
        &self.description
    }
}
