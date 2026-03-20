use crate::config::Location;
use crate::transaction::{Transaction, TransactionList, TransferOptions};

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
        for snapshot in SequenceComparison::from_datasets(source_dataset, target_dataset)?
            .free_iter(source_dataset.get_snapshot_option_overlap()?)?
        {
            transactions.push(
                Transaction::new_destroy_snapshot(
                    source,
                    source_dataset.get_name_ref().to_string(),
                    snapshot.to_string(),
                )
                .map_err(EngineError::TransactionError)?,
            );
        }
        Ok(transactions)
    }

    pub fn get_sync_transactions(
        &self,
        source: &Location,
        target: &Location,
        direct: bool,
        options: &TransferOptions,
    ) -> Result<TransactionList, EngineError> {
        match (self.source, self.target) {
            (None, None | Some(_)) => Ok(TransactionList::new()),
            (Some(source_dataset), None) => {
                Self::get_sync_transactions_new(source, target, source_dataset, direct, options)
            }
            (Some(source_dataset), Some(target_dataset)) => Self::get_sync_transactions_followup(
                source,
                target,
                source_dataset,
                target_dataset,
                direct,
                options,
            ),
        }
    }

    fn get_sync_transactions_new(
        source: &Location,
        target: &Location,
        source_dataset: &Dataset,
        direct: bool,
        options: &TransferOptions,
    ) -> Result<TransactionList, EngineError> {
        if source_dataset.len() == 0 {
            return Err(EngineError::DatasetWithoutSnapshotError);
        }
        let mut transactions = TransactionList::new();
        if !source_dataset.get_sync_option()? {
            return Ok(transactions);
        }
        if source_dataset.len() > 0 {
            transactions.push(
                Transaction::new_transfer_initial(
                    source,
                    target,
                    source_dataset.get_name_ref().to_string(),
                    source_dataset
                        .get_snapshot_ref_by_index(0)
                        .unwrap()
                        .get_name_ref()
                        .to_string(),
                    direct,
                    options,
                )
                .map_err(EngineError::TransactionError)?,
            );
        }
        for idx in 0..source_dataset.len() - 1 {
            transactions.push(
                Transaction::new_transfer_incremental(
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
                    direct,
                    options,
                )
                .map_err(EngineError::TransactionError)?,
            );
        }
        Ok(transactions)
    }

    fn get_sync_transactions_followup(
        source: &Location,
        target: &Location,
        source_dataset: &Dataset,
        target_dataset: &Dataset,
        direct: bool,
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
                Transaction::new_transfer_incremental(
                    source,
                    target,
                    source_dataset.get_name_ref().to_string(),
                    from_snapshot.to_string(),
                    to_snapshot.to_string(),
                    direct,
                    options,
                )
                .map_err(EngineError::TransactionError)?,
            );
        }
        Ok(transactions)
    }
}
