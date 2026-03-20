use std::collections::HashSet;

use crate::transaction::{TransactionList, TransferOptions};

use super::super::apool::Apool;
use super::super::common::Common;
use super::super::errors::EngineError;

use super::dataset::DatasetComparison;

pub struct ApoolComparison<'a> {
    source: &'a Apool,
    target: &'a Apool,
}

impl ApoolComparison<'_> {
    #[must_use]
    pub const fn new<'a>(source: &'a Apool, target: &'a Apool) -> ApoolComparison<'a> {
        ApoolComparison { source, target }
    }

    pub fn get_free_transactions(&self) -> Result<TransactionList, EngineError> {
        let mut transactions: TransactionList = TransactionList::new();
        for dataset_comparison in self.get_dataset_comparisons_iter() {
            let mut sub =
                dataset_comparison.get_free_transactions(self.source.get_location_ref())?;
            transactions.append(&mut sub);
        }
        Ok(transactions)
    }

    fn get_unique_dataset_names(&self) -> Vec<&str> {
        let mut uniques: HashSet<&str> = HashSet::new();
        self.source
            .get_dataset_iter()
            .for_each(|dataset| _ = uniques.insert(dataset.get_name_ref()));
        self.target
            .get_dataset_iter()
            .for_each(|dataset| _ = uniques.insert(dataset.get_name_ref()));
        let mut uniques: Vec<&str> = uniques.drain().collect();
        uniques.sort_unstable();
        uniques
    }

    fn get_dataset_comparisons_iter(&'_ self) -> impl Iterator<Item = DatasetComparison<'_>> {
        self.get_unique_dataset_names().into_iter().map(|name| {
            DatasetComparison::new(
                self.source.get_dataset_ref(name),
                self.target.get_dataset_ref(name),
            )
        })
    }

    pub fn get_sync_transactions(
        &self,
        direct: bool,
        options: &TransferOptions,
    ) -> Result<TransactionList, EngineError> {
        let mut transactions: TransactionList = TransactionList::new();
        for dataset_comparison in self.get_dataset_comparisons_iter() {
            let mut sub = dataset_comparison.get_sync_transactions(
                self.source.get_location_ref(),
                self.target.get_location_ref(),
                direct,
                options,
            )?;
            transactions.append(&mut sub);
        }
        Ok(transactions)
    }
}
