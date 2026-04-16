use crate::config::Location;
use crate::output::{colorized_storage_si_suffix, storage_si_suffix, storage_suffix};
use crate::subprocess::Command;

use super::super::basebuilder::BaseBuilder;
use super::super::basemeta::BaseMeta;
use super::super::errors::TransactionBuildError;
use super::super::meta::TransactionMeta;
use super::super::transaction::Transaction;

#[derive(Clone)]
pub struct CreateSnapshotMeta {
    pub host: String,
    pub written: u64,
    pub dataset: String,
    pub snapshot: String,
}

impl BaseMeta for CreateSnapshotMeta {
    fn to_description(&self, color: bool, si: bool) -> String {
        format!(
            "create snapshot: {}:{}@{} ({})",
            self.host,
            self.dataset,
            self.snapshot,
            if si {
                if color {
                    colorized_storage_si_suffix(self.written)
                } else {
                    storage_si_suffix(self.written)
                }
            } else {
                storage_suffix(self.written)
            },
        )
    }
}

pub struct CreateSnapshotBuilder<'a> {
    location: &'a Location,
    dataset: String,
    snapshot: String,
    written: u64,
}

impl<'a> CreateSnapshotBuilder<'a> {
    #[must_use]
    pub const fn new(
        location: &'a Location,
        dataset: String,
        snapshot: String,
        written: u64,
    ) -> Self {
        Self {
            location,
            dataset,
            snapshot,
            written,
        }
    }
}

impl BaseBuilder for CreateSnapshotBuilder<'_> {
    fn build(self) -> Result<Transaction, TransactionBuildError> {
        let dataset_name = if self.dataset == "/" { "" } else { &self.dataset };
        let argument = format!(
            "{}{}@{}",
            self.location.get_root_ref().as_str(),
            dataset_name,
            self.snapshot
        );
        Ok(Transaction::new(
            TransactionMeta::CreateSnapshot(CreateSnapshotMeta {
                host: self.location.get_route_ref().get_host_ref().to_string(),
                written: self.written,
                dataset: self.dataset,
                snapshot: self.snapshot,
            }),
            Command::new(
                    "zfs".to_string(),
                    vec![
                        "snapshot".to_string(),
                        argument,
                    ],
                )
                .map_err(TransactionBuildError::Subprocess)?
                .on_route(self.location.get_route_ref())
                .map_err(TransactionBuildError::Subprocess)?,
            true,
        ))
    }
}
