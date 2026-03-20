use super::super::common::Common;
use super::super::snapshot::Snapshot;

pub struct SnapshotComparison {
    name: String,
    source: Option<usize>,
    target: Option<usize>,
    creation: i64,
}

impl SnapshotComparison {
    pub const fn new(name: String, creation: i64) -> Self {
        Self {
            name,
            source: None,
            target: None,
            creation,
        }
    }

    pub fn from_source_snapshot(position: usize, snapshot: &Snapshot) -> Self {
        Self::new(snapshot.get_name_ref().to_string(), snapshot.get_creation())
            .with_source(position)
    }

    pub fn from_target_snapshot(position: usize, snapshot: &Snapshot) -> Self {
        Self::new(snapshot.get_name_ref().to_string(), snapshot.get_creation())
            .with_target(position)
    }

    pub const fn get_creation(&self) -> i64 {
        self.creation
    }

    pub fn get_name_ref(&self) -> &str {
        &self.name
    }

    pub const fn is_on_both(&self) -> bool {
        self.is_on_source() && self.is_on_target()
    }

    pub const fn is_on_source(&self) -> bool {
        self.source.is_some()
    }

    pub const fn is_on_target(&self) -> bool {
        self.target.is_some()
    }

    pub const fn with_source(mut self, idx: usize) -> Self {
        self.source = Some(idx);
        self
    }

    pub const fn with_target(mut self, idx: usize) -> Self {
        self.target = Some(idx);
        self
    }
}
