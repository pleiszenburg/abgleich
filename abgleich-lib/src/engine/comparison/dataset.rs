use crate::config::{Location, TransferOptions};
use crate::transaction::{
    BaseBuilder, DestroySnapshotBuilder, TransactionList, TransferIncrementalBuilder,
    TransferInitialBuilder,
};

use super::super::common::Common;
use super::super::dataset::Dataset;
use super::super::errors::EngineError;

use super::sequence::SequenceComparison;

pub struct DatasetComparison<'a> {
    source: Option<&'a Dataset>,
    target: Option<&'a Dataset>,
}

impl<'a> DatasetComparison<'a> {
    pub const fn new(source: Option<&'a Dataset>, target: Option<&'a Dataset>) -> Self {
        Self { source, target }
    }

    pub fn get_free_transactions(&self, source: &Location) -> Result<TransactionList, EngineError> {
        let (source_dataset, target_dataset) = match (self.source, self.target) {
            (None | Some(_), None) | (None, Some(_)) => return Ok(TransactionList::new()),
            (Some(source_dataset), Some(target_dataset)) => (source_dataset, target_dataset),
        };
        let mut transactions = TransactionList::new();
        if !source_dataset.get_sync_option()? {
            return Ok(transactions);
        }
        for snapshot in SequenceComparison::from_datasets(source_dataset, target_dataset)?
            .free_iter(source_dataset.get_snapshot_option_overlap()?)?
        {
            transactions.push(
                DestroySnapshotBuilder::new(
                    source,
                    source_dataset.get_name_ref().to_string(),
                    snapshot.to_string(),
                )
                .build()
                .map_err(EngineError::TransactionBuild)?,
            );
        }
        Ok(transactions)
    }

    pub fn get_sync_transactions(
        &self,
        source: &Location,
        target: &Location,
        options: &TransferOptions,
    ) -> Result<TransactionList, EngineError> {
        match (self.source, self.target) {
            (None, None | Some(_)) => Ok(TransactionList::new()),
            (Some(source_dataset), None) => {
                Self::get_sync_transactions_new(source, target, source_dataset, options)
            }
            (Some(source_dataset), Some(target_dataset)) => Self::get_sync_transactions_followup(
                source,
                target,
                source_dataset,
                target_dataset,
                options,
            ),
        }
    }

    fn get_sync_transactions_new(
        source: &Location,
        target: &Location,
        source_dataset: &Dataset,
        options: &TransferOptions,
    ) -> Result<TransactionList, EngineError> {
        let mut transactions = TransactionList::new();
        if !source_dataset.get_sync_option()? {
            return Ok(transactions);
        }
        if source_dataset.len() == 0 {
            return Err(EngineError::DatasetWithoutSnapshot {
                dataset: source_dataset.get_name_ref().to_string(),
            });
        }
        if source_dataset.len() > 0 {
            transactions.push(
                TransferInitialBuilder::new(
                    source,
                    target,
                    source_dataset.get_name_ref().to_string(),
                    source_dataset
                        .get_snapshot_ref_by_index(0)
                        .unwrap()
                        .get_name_ref()
                        .to_string(),
                    options,
                )
                .build()
                .map_err(EngineError::TransactionBuild)?,
            );
        }
        for idx in 0..source_dataset.len() - 1 {
            transactions.push(
                TransferIncrementalBuilder::new(
                    source,
                    target,
                    source_dataset.get_name_ref().to_string(),
                    source_dataset
                        .get_snapshot_ref_by_index(idx)
                        .unwrap()
                        .get_name_ref()
                        .to_string(),
                    source_dataset
                        .get_snapshot_ref_by_index(idx + 1)
                        .unwrap()
                        .get_name_ref()
                        .to_string(),
                    options,
                )
                .build()
                .map_err(EngineError::TransactionBuild)?,
            );
        }
        Ok(transactions)
    }

    fn get_sync_transactions_followup(
        source: &Location,
        target: &Location,
        source_dataset: &Dataset,
        target_dataset: &Dataset,
        options: &TransferOptions,
    ) -> Result<TransactionList, EngineError> {
        let mut transactions = TransactionList::new();
        if !source_dataset.get_sync_option()? {
            return Ok(transactions);
        }
        for (from_snapshot, to_snapshot) in
            SequenceComparison::from_datasets(source_dataset, target_dataset)?.sync_iter()?
        {
            transactions.push(
                TransferIncrementalBuilder::new(
                    source,
                    target,
                    source_dataset.get_name_ref().to_string(),
                    from_snapshot.to_string(),
                    to_snapshot.to_string(),
                    options,
                )
                .build()
                .map_err(EngineError::TransactionBuild)?,
            );
        }
        Ok(transactions)
    }
}
