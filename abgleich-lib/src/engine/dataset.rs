use std::str::FromStr;

use chrono::{DateTime, Utc};
use indexmap::IndexMap;
use indexmap::map::Values;
use tracing::debug;

use crate::config::Location;
use crate::consts::{
    DEFAULT_DIFF, DEFAULT_FORMAT, DEFAULT_OVERLAP, DEFAULT_SNAP, DEFAULT_SYNC, DEFAULT_THRESHOLD,
    VAR_DIFF, VAR_FORMAT, VAR_OVERLAP, VAR_SNAP, VAR_SYNC, VAR_THRESHOLD,
};
use crate::property::{BaseProperty, Description, SnapValue, TypeValue};
use crate::sys::{envvar2bool, envvar2string, envvar2type};
use crate::transaction::{BaseBuilder, CreateSnapshotBuilder, DiffBuilder, Transaction};

use super::common::Common;
use super::errors::EngineError;
use super::snapshot::Snapshot;

pub struct Dataset {
    description: Description,
    snapshots: IndexMap<String, Snapshot>,
}

impl Dataset {
    pub fn from_description(description: Description) -> Self {
        Self {
            description,
            snapshots: IndexMap::new(),
        }
    }

    fn contains_changes(&self, location: &Location) -> Result<bool, EngineError> {
        let written = self.description.written.as_ref().ok_or(
            EngineError::UnknownWritten { root: location.get_root_ref().to_string(), name: self.description.name.clone() }
        )?.get_value_ref().unpack();
        debug!(contains_changes = "start", written = written);
        if *written == 0 {
            debug!(contains_changes = "exit", written = 0);
            return Ok(false);
        }
        if self.description.type_.as_ref().ok_or(
            EngineError::DatasetTypeUnknown { root: location.get_root_ref().to_string(), name: self.description.name.clone() }
        )?.get_value_ref() == &TypeValue::Volume {
            debug!(contains_changes = "exit", type_ = "volume");
            return Ok(true);
        }
        let threshold = self.get_snapshot_option_threshold()?;
        if threshold < *written {
            debug!(contains_changes = "exit", threshold = threshold);
            return Ok(true);
        }
        if !self.get_snapshot_option_diff()? {
            debug!(contains_changes = "exit", diff = "off");
            return Ok(true);
        }
        debug!(contains_changes = "diff");
        let outcome = DiffBuilder::new(
            location,
            self.description.name.clone(),
            self.snapshots
                .values()
                .last()
                .unwrap()
                .get_name_ref()
                .to_string(),
        )
        .build()
        .map_err(EngineError::TransactionBuild)?
        .run()
        .map_err(EngineError::TransactionRun)?;
        outcome
            .assert_success()
            .map_err(EngineError::TransactionRun)?;
        Ok(!outcome
            .get_data_ref()
            .unwrap() // safe operation
            .trim_matches([' ', '\n', '\t'])
            .is_empty())
    }

    pub fn generate_snapshot_name(&self, timestamp: Option<DateTime<Utc>>) -> String {
        let timestamp = timestamp.unwrap_or_else(Utc::now);
        timestamp
            .format(&self.get_snapshot_option_format())
            .to_string()
    }

    pub fn get_create_snapshot_transaction(
        &self,
        location: &Location,
        snapshot: String,
    ) -> Result<Transaction, EngineError> {
        CreateSnapshotBuilder::new(
            location,
            self.description.name.clone(),
            snapshot,
            *self.description
                .written
                .as_ref()
                .ok_or(EngineError::UnknownWritten{
                    name: self.get_name_ref().to_string(),
                    root: location.get_root_ref().to_string(),
                })?
                .get_value_ref()
                .unpack(),
        )
        .build()
        .map_err(EngineError::TransactionBuild)
    }

    pub fn get_last_snapshot_ref(&self) -> Option<&Snapshot> {
        self.snapshots.values().last()
    }

    pub fn get_snapshot_names_iter(&self) -> impl Iterator<Item = &str> {
        self.get_snapshots_iter()
            .map(super::common::Common::get_name_ref)
    }

    fn get_snapshot_option_diff(&self) -> Result<bool, EngineError> {
        Ok(envvar2bool(VAR_DIFF)
            .map_err(|e| EngineError::EnvironmentVariable { name: VAR_DIFF.to_string(), source: e })?
            .unwrap_or_else(|| {
                self.description.abgleich_diff.as_ref().map_or(
                    DEFAULT_DIFF,
                    |value| bool::from(value.get_value_ref())
                )
            })
        )
    }

    fn get_snapshot_option_format(&self) -> String {
        envvar2string(VAR_FORMAT).unwrap_or_else(|| {
            self.description.abgleich_format.as_ref().map_or_else(
                || DEFAULT_FORMAT.to_owned(),
                |value| value.get_value_ref().to_string()
            )
        })
    }

    pub fn get_snapshot_option_overlap(&self) -> Result<i64, EngineError> {
        Ok(envvar2type::<i64>(VAR_OVERLAP)
            .map_err(|e| EngineError::EnvironmentVariable { name: VAR_OVERLAP.to_string(), source: e })?
            .unwrap_or_else(|| {
                self.description.abgleich_overlap.as_ref().map_or(
                    DEFAULT_OVERLAP,
                    |value| *value.get_value_ref().unpack()
                )
            })
        )
    }

    pub fn get_snapshot_option_snap(&self) -> Result<SnapValue, EngineError> {
        Ok(match envvar2string(VAR_SNAP) {
            Some(env_value) => SnapValue::from_str(&env_value).map_err(
                |e| EngineError::Value { name: "env(abgleich:snap)".to_string(), source: e }
            )?,
            None => match &self.description.abgleich_snap {
                Some(value) => value.get_value_ref().clone(),
                _ => SnapValue::from_str(DEFAULT_SNAP).map_err(
                    |e| EngineError::Value { name: "default(abgleich:snap)".to_string(), source: e }
                )?,
            },
        })
    }

    fn get_snapshot_option_threshold(&self) -> Result<u64, EngineError> {
        Ok(envvar2type::<u64>(VAR_THRESHOLD)
            .map_err(|e| EngineError::EnvironmentVariable { name: VAR_THRESHOLD.to_string(), source: e })?
            .unwrap_or_else(|| {
                self.description.abgleich_threshold.as_ref().map_or(
                    DEFAULT_THRESHOLD,
                    |value| *value.get_value_ref().unpack()
                )
            })
        )
    }

    pub fn get_snapshot_position(&self, name: &str) -> Option<usize> {
        self.snapshots
            .iter()
            .position(|(_, snapshot)| snapshot.get_name_ref() == name)
    }

    pub fn get_snapshot_positions_iter(
        &self,
        names: &Vec<&str>,
    ) -> impl Iterator<Item = Option<usize>> {
        names.iter().map(|name| {
            self.snapshots
                .iter()
                .position(|(_, snapshot)| snapshot.get_name_ref() == *name)
        })
    }

    pub fn get_snapshot_ref_by_index(&self, idx: usize) -> Option<&Snapshot> {
        match self.snapshots.get_index(idx) {
            Some((_, snapshot)) => Some(snapshot),
            _ => None,
        }
    }

    pub fn get_snapshot_ref_by_name(&self, name: &str) -> Option<&Snapshot> {
        self.snapshots.get(name)
    }

    pub fn get_snapshots_enumerated_after_name_iter(
        &self,
        name: &str,
    ) -> impl Iterator<Item = (usize, &Snapshot)> {
        let start = self.get_snapshot_position(name).unwrap_or(self.len()) + 1; // HACK use len for empty iterator if no match is found
        self.snapshots[start..]
            .iter()
            .enumerate()
            .map(move |(idx, (_, snapshot))| (idx + start, snapshot))
    }

    pub fn get_snapshots_enumerated_before_name_iter(
        &self,
        name: &str,
    ) -> impl Iterator<Item = (usize, &Snapshot)> {
        let (start, stop) = self.get_snapshot_position(name).map_or_else(
            || (self.len(), self.len()), // HACK use len for empty iterator if no match is found
            |position| (0usize, position),
        );
        self.snapshots[start..stop]
            .iter()
            .enumerate()
            .map(move |(idx, (_, snapshot))| (idx + start, snapshot))
    }

    pub fn get_snapshots_enumerated_between_names_iter(
        &self,
        start: &str,
        stop: &str,
    ) -> impl Iterator<Item = (usize, &Snapshot)> {
        let start = self.get_snapshot_position(start).unwrap_or(self.len()) + 1; // HACK use len for empty iterator if no match is found
        let stop = self.get_snapshot_position(stop).unwrap_or(0); // HACK use zero for empty iterator if no match is found
        self.snapshots[start..stop]
            .iter()
            .enumerate()
            .map(move |(idx, (_, snapshot))| (idx + start, snapshot))
    }

    pub fn get_snapshots_enumerated_iter(&self) -> impl Iterator<Item = (usize, &Snapshot)> {
        self.snapshots.values().enumerate()
    }

    pub fn get_snapshots_iter(&self) -> Values<'_, String, Snapshot> {
        self.snapshots.values()
    }

    pub fn get_sync_option(&self) -> Result<bool, EngineError> {
        Ok(envvar2bool(VAR_SYNC)
            .map_err(|e| EngineError::EnvironmentVariable { name: VAR_SYNC.to_string(), source: e })?
            .unwrap_or_else(|| {
                self.description.abgleich_sync.as_ref().map_or(
                    DEFAULT_SYNC,
                    |value| bool::from(value.get_value_ref())
                )
            })
        )
    }

    pub fn is_snapshot_creation_monotonic(&self) -> bool {
        self.snapshots
            .values()
            .zip(self.snapshots.values().skip(1))
            .all(|(a, b)| a.get_creation() <= b.get_creation())
    }

    pub fn is_snapshot_intended(&self, location: &Location) -> Result<bool, EngineError> {
        match self.get_snapshot_option_snap()? {
            SnapValue::Always => Ok(true),
            SnapValue::Changed => {
                if self.snapshots.is_empty() {
                    return Ok(true);
                }
                if self.contains_changes(location)? {
                    return Ok(true);
                }
                Ok(false)
            }
            SnapValue::Never => Ok(false),
        }
    }

    pub fn len(&self) -> usize {
        self.snapshots.len()
    }

    pub fn push_snapshot(&mut self, snapshot: Snapshot) {
        self.snapshots
            .insert(snapshot.get_name_ref().to_string(), snapshot);
    }
}

impl Common for Dataset {
    fn get_description_ref(&self) -> &Description {
        &self.description
    }
}
