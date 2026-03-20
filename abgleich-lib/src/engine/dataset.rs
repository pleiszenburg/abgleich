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
use crate::sys::{envvar2bool, envvar2string, envvar2type};
use crate::transaction::Transaction;

use super::common::Common;
use super::errors::EngineError;
use super::meta::Meta;
use super::property::{Snap, Type};
use super::snapshot::Snapshot;

pub struct Dataset {
    meta: Meta,
    snapshots: IndexMap<String, Snapshot>,
}

impl Dataset {
    pub fn from_meta(meta: Meta) -> Self {
        Self {
            meta,
            snapshots: IndexMap::new(),
        }
    }

    fn contains_changes(&self, location: &Location) -> Result<bool, EngineError> {
        let written = self.meta.written.get_uint()?.unwrap();
        debug!(contains_changes = "start", written = written);
        if written == 0 {
            debug!(contains_changes = "exit", written = 0);
            return Ok(false);
        }
        if self.meta.type_.get_type()?.unwrap() == Type::Volume {
            debug!(contains_changes = "exit", type_ = "volume");
            return Ok(true);
        }
        let threshold = self.get_snapshot_option_threshold()?;
        if threshold < written {
            debug!(contains_changes = "exit", threshold = threshold);
            return Ok(true);
        }
        if !self.get_snapshot_option_diff()? {
            debug!(contains_changes = "exit", diff = "off");
            return Ok(true);
        }
        debug!(contains_changes = "diff");
        let outcome = Transaction::new_diff(
            location,
            self.meta.name.clone(),
            self.snapshots
                .values()
                .last()
                .unwrap()
                .get_name_ref()
                .to_string(),
        )
        .map_err(EngineError::TransactionError)?
        .run()
        .map_err(EngineError::TransactionError)?;
        outcome
            .assert_success()
            .map_err(EngineError::TransactionError)?;
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
        Transaction::new_create_snapshot(
            location,
            self.meta.name.clone(),
            snapshot,
            self.meta
                .written
                .get_uint()?
                .ok_or(EngineError::PropertyUnknownError)?,
        )
        .map_err(EngineError::TransactionError)
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
            .map_err(EngineError::SysError)?
            .unwrap_or_else(|| {
                self.meta
                    .abgleich_diff
                    .get_bool()
                    .unwrap()
                    .map_or(DEFAULT_DIFF, |prop_value| prop_value)
            }))
    }

    fn get_snapshot_option_format(&self) -> String {
        envvar2string(VAR_FORMAT).unwrap_or_else(|| {
            self.meta
                .abgleich_format
                .get_string_ref()
                .unwrap()
                .map_or_else(|| DEFAULT_FORMAT.to_owned(), std::borrow::ToOwned::to_owned)
        })
    }

    pub fn get_snapshot_option_overlap(&self) -> Result<i64, EngineError> {
        Ok(envvar2type::<i64>(VAR_OVERLAP)
            .map_err(EngineError::SysError)?
            .unwrap_or_else(|| {
                self.meta
                    .abgleich_overlap
                    .get_int()
                    .unwrap()
                    .map_or(DEFAULT_OVERLAP, |prop_value| prop_value)
            }))
    }

    pub fn get_snapshot_option_snap(&self) -> Result<Snap, EngineError> {
        Ok(match envvar2string(VAR_SNAP) {
            Some(env_value) => Snap::from_str(&env_value)?,
            _ => match self.meta.abgleich_snap.get_snap().unwrap() {
                Some(prop_value) => prop_value,
                _ => Snap::from_str(DEFAULT_SNAP)?,
            },
        })
    }

    fn get_snapshot_option_threshold(&self) -> Result<u64, EngineError> {
        Ok(envvar2type::<u64>(VAR_THRESHOLD)
            .map_err(EngineError::SysError)?
            .unwrap_or_else(|| {
                self.meta
                    .abgleich_threshold
                    .get_uint()
                    .unwrap()
                    .map_or(DEFAULT_THRESHOLD, |prop_value| prop_value)
            }))
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
            .map_err(EngineError::SysError)?
            .unwrap_or_else(|| {
                self.meta
                    .abgleich_sync
                    .get_bool()
                    .unwrap()
                    .map_or(DEFAULT_SYNC, |prop_value| prop_value)
            }))
    }

    pub fn is_snapshot_creation_monotonic(&self) -> bool {
        self.snapshots
            .values()
            .zip(self.snapshots.values().skip(1))
            .all(|(a, b)| a.get_creation() <= b.get_creation())
    }

    pub fn is_snapshot_intended(&self, location: &Location) -> Result<bool, EngineError> {
        match self.get_snapshot_option_snap()? {
            Snap::Always => Ok(true),
            Snap::Changed => {
                if self.snapshots.is_empty() {
                    return Ok(true);
                }
                if self.contains_changes(location)? {
                    return Ok(true);
                }
                Ok(false)
            }
            Snap::Never => Ok(false),
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
    fn get_meta_ref(&self) -> &Meta {
        &self.meta
    }
}
