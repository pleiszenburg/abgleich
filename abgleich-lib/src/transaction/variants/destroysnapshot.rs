use crate::config::Location;
use crate::subprocess::Command;

use super::super::basebuilder::BaseBuilder;
use super::super::basemeta::BaseMeta;
use super::super::errors::TransactionBuildError;
use super::super::meta::TransactionMeta;
use super::super::transaction::Transaction;

#[derive(Clone)]
pub struct DestroySnapshotMeta {
    pub host: String,
    pub dataset: String,
    pub snapshot: String,
}

impl BaseMeta for DestroySnapshotMeta {
    fn to_description(&self, _color: bool, _si: bool) -> String {
        format!(
            "destroy snapshot: {}:{}@{}",
            self.host, self.dataset, self.snapshot,
        )
    }
}

pub struct DestroySnapshotBuilder<'a> {
    location: &'a Location,
    dataset: String,
    snapshot: String,
}

impl<'a> DestroySnapshotBuilder<'a> {
    #[must_use]
    pub const fn new(location: &'a Location, dataset: String, snapshot: String) -> Self {
        Self {
            location,
            dataset,
            snapshot,
        }
    }
}

impl BaseBuilder for DestroySnapshotBuilder<'_> {
    fn build(self) -> Result<Transaction, TransactionBuildError> {
        let dataset_name = if self.dataset == "/" {
            ""
        } else {
            &self.dataset
        };
        let argument = format!(
            "{}{}@{}",
            self.location.get_root_ref().as_str(),
            dataset_name,
            self.snapshot
        );
        Ok(Transaction::new(
            TransactionMeta::DestroySnapshot(DestroySnapshotMeta {
                host: self.location.get_route_ref().get_host_ref().to_string(),
                dataset: self.dataset,
                snapshot: self.snapshot,
            }),
            Command::new("zfs".to_string(), vec!["destroy".to_string(), argument])
                .map_err(TransactionBuildError::Subprocess)?
                .on_route(self.location.get_route_ref())
                .map_err(TransactionBuildError::Subprocess)?,
            true,
        ))
    }
}
