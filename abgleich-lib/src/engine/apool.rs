use colored::Colorize;
use indexmap::IndexMap;
use indexmap::map::Values;
use serde_json::json;

use crate::config::Location;
use crate::output::{Alignment, Table, TableColumn, colorized_storage_si_suffix};
use crate::transaction::{Transaction, TransactionList};

use super::common::Common;
use super::dataset::Dataset;
use super::errors::EngineError;
use super::meta::Meta;
use super::property::Type;
use super::snapshot::Snapshot;

pub struct Apool {
    location: Location,
    datasets: IndexMap<String, Dataset>,
}

impl Apool {
    pub fn from_location(location: Location) -> Result<Self, EngineError> {
        let outcome = Transaction::new_inventory(&location)
            .map_err(EngineError::TransactionError)?
            .run()
            .map_err(EngineError::TransactionError)?;
        outcome
            .assert_success()
            .map_err(EngineError::TransactionError)?;
        Self::from_raw(
            location,
            #[expect(clippy::missing_panics_doc, reason = "infallible")]
            outcome.get_data_ref().unwrap(),
        )
    }

    pub fn from_raw(location: Location, raw: &str) -> Result<Self, EngineError> {
        let mut metas = Meta::from_raws(raw)?;
        let mut dataset_names: Vec<String> = Vec::new();
        let mut snapshot_names: Vec<String> = Vec::new();
        for (name, meta) in &metas {
            match meta
                .type_
                .get_type()?
                .ok_or(EngineError::DatasetTypeUnknownError)?
            {
                Type::Snapshot => snapshot_names.push(name.clone()),
                _ => dataset_names.push(name.clone()),
            }
        }
        metas.reverse(); // a bit of performance later on, i.e. less shifting?
        let mut datasets = IndexMap::new();
        for name in dataset_names {
            let mut meta = {
                #[expect(clippy::missing_panics_doc, reason = "infallible")]
                metas.shift_remove(&name).unwrap()
            };
            meta.fix_dataset_relative(location.get_root_ref().as_str());
            datasets.insert(meta.name.clone(), Dataset::from_meta(meta));
        }
        for name in snapshot_names {
            let mut meta = {
                #[expect(clippy::missing_panics_doc, reason = "infallible")]
                metas.shift_remove(&name).unwrap()
            };
            let parent = meta.fix_snapshot_relative(location.get_root_ref().as_str());
            datasets
                .get_mut(&parent)
                .ok_or(EngineError::DatasetUnknownError)?
                .push_snapshot(Snapshot::new(meta));
        }
        Ok(Self { location, datasets })
    }

    pub fn get_create_snapshot_transactions(&self) -> Result<TransactionList, EngineError> {
        let mut transactions = TransactionList::new();
        for dataset in self.datasets.values() {
            if dataset.is_snapshot_intended(&self.location)? {
                transactions.push(dataset.get_create_snapshot_transaction(
                    &self.location,
                    dataset.generate_snapshot_name(None),
                )?);
            }
        }
        Ok(transactions)
    }

    #[must_use]
    pub fn get_dataset_iter(&self) -> Values<'_, String, Dataset> {
        self.datasets.values()
    }

    #[must_use]
    pub fn get_dataset_ref(&self, name: &str) -> Option<&Dataset> {
        self.datasets.get(name)
    }

    pub fn get_dataset_names_iter(&self) -> impl Iterator<Item = &str> {
        self.get_dataset_iter()
            .map(super::common::Common::get_name_ref)
    }

    #[must_use]
    pub const fn get_location_ref(&self) -> &Location {
        &self.location
    }

    #[must_use]
    pub fn is_empty(&self) -> bool {
        self.datasets.is_empty()
    }

    #[must_use]
    pub fn len(&self) -> usize {
        self.datasets.len()
    }

    pub fn print_json(&self) -> Result<(), EngineError> {
        for dataset in self.datasets.values() {
            println!(
                "{}",
                json!({
                    "name": format!(
                        "{}:{}{}",
                        self.location.get_route_ref().get_host_ref(),
                        self.location.get_root_ref().as_str(),
                        dataset.get_name_ref()
                    ),
                    "type": dataset.get_type().to_string(),
                    "snap": dataset.get_snapshot_option_snap()?.to_string(),
                    "used": dataset.get_used(),
                    "referenced": dataset.get_referenced(),
                    "compressratio": dataset.get_compressratio(),
                })
            );
            let dataset_prefix = format!(
                "{}:{}{}@",
                self.location.get_route_ref().get_host_ref(),
                self.location.get_root_ref().as_str(),
                dataset.get_name_ref()
            );
            for snapshot in dataset.get_snapshots_iter() {
                println!(
                    "{}",
                    json!({
                        "name": format!(
                            "{}{}",
                            dataset_prefix,
                            snapshot.get_name_ref()
                        ),
                        "type": snapshot.get_type().to_string(),
                        "used": snapshot.get_used(),
                        "referenced": snapshot.get_referenced(),
                        "compressratio": snapshot.get_compressratio(),
                    })
                );
            }
        }
        Ok(())
    }

    pub fn print_table(&self) -> Result<(), EngineError> {
        let mut table = Table::new(vec![
            TableColumn::new("name".to_string(), Alignment::Left),
            TableColumn::new("t".to_string(), Alignment::Left),
            TableColumn::new("s".to_string(), Alignment::Left),
            TableColumn::new("used".to_string(), Alignment::Right),
            TableColumn::new("referenced".to_string(), Alignment::Right),
            TableColumn::new("compressratio".to_string(), Alignment::Right),
        ]);
        for dataset in self.datasets.values() {
            table.push_row(vec![
                format!(
                    "{}{}{}{}",
                    self.location.get_route_ref().get_host_ref().bright_black(),
                    ":".bright_black(),
                    self.location.get_root_ref().as_str().bright_black(),
                    dataset.get_name_ref()
                ),
                dataset.get_type().to_char(),
                dataset.get_snapshot_option_snap()?.to_char(),
                colorized_storage_si_suffix(dataset.get_used()),
                colorized_storage_si_suffix(dataset.get_referenced()),
                format!("{:.02}", dataset.get_compressratio()),
            ]);
            let dataset_prefix = format!(
                "{}:{}{}@",
                self.location.get_route_ref().get_host_ref(),
                self.location.get_root_ref().as_str(),
                dataset.get_name_ref()
            )
            .bright_black();
            for snapshot in dataset.get_snapshots_iter() {
                table.push_row(vec![
                    format!(
                        "{}{}",
                        dataset_prefix,
                        snapshot.get_name_ref().bright_purple()
                    ),
                    snapshot.get_type().to_char(),
                    " ".to_string(),
                    colorized_storage_si_suffix(snapshot.get_used()),
                    colorized_storage_si_suffix(snapshot.get_referenced()),
                    format!("{:.02}", snapshot.get_compressratio()),
                ]);
            }
        }
        table.print();
        Ok(())
    }
}
