use std::collections::HashSet;

use crate::engine::Common;

use super::super::dataset::Dataset;
use super::super::errors::EngineError;

use super::snapshot::SnapshotComparison;

struct SequenceBuilder<'a> {
    source: &'a Dataset,
    target: &'a Dataset,
}

impl<'a> SequenceBuilder<'a> {
    pub const fn from_datasets(source: &'a Dataset, target: &'a Dataset) -> Self {
        Self { source, target }
    }

    pub fn build(&self) -> Result<Vec<SnapshotComparison>, EngineError> {
        if !self.source.is_snapshot_creation_monotonic()
            || !self.target.is_snapshot_creation_monotonic()
        {
            return Err(EngineError::DatasetSnapshotCreationNotMonotonicError);
        }
        let common = Self::sort_snapshot_names(self.get_common_snapshot_names(), self.source);
        if common.is_empty() {
            return Ok(self.uncommon_datasets());
        }
        self.assert_common_order(&common)?;
        let mut sequence = Vec::new();
        sequence.append(self.get_sequence_before(common[0]).as_mut());
        for (start, stop) in common.iter().zip(common.iter().skip(1)) {
            sequence.push(self.get_common_comparison(start)?);
            sequence.append(self.get_sequence_between(start, stop).as_mut());
        }
        sequence.push(self.get_common_comparison(common.last().unwrap())?);
        sequence.append(self.get_sequence_after(common.last().unwrap()).as_mut());
        Ok(sequence)
    }

    fn uncommon_datasets(&self) -> Vec<SnapshotComparison> {
        let mut sequence = Vec::new();
        self.source
            .get_snapshots_enumerated_iter()
            .for_each(|(position, snapshot)| {
                sequence.push(SnapshotComparison::from_source_snapshot(position, snapshot));
            });
        self.target
            .get_snapshots_enumerated_iter()
            .for_each(|(position, snapshot)| {
                sequence.push(SnapshotComparison::from_target_snapshot(position, snapshot));
            });
        sequence.sort_by_key(super::snapshot::SnapshotComparison::get_creation);
        sequence
    }

    fn assert_common_order(&self, common: &[&str]) -> Result<(), EngineError> {
        let source_names: Vec<&str> = common.to_owned(); // common sorted by source
        let target_names: Vec<&str> = common.to_owned();
        let target_names = Self::sort_snapshot_names(target_names, self.target);
        for (source_name, target_name) in source_names.iter().zip(target_names.iter()) {
            if **source_name != **target_name {
                return Err(EngineError::DatasetSnapshotSequenceValidationError);
            }
        }
        Ok(())
    }

    fn get_common_comparison(&self, name: &str) -> Result<SnapshotComparison, EngineError> {
        let source_snapshot = self.source.get_snapshot_ref_by_name(name).unwrap();
        let target_snapshot = self.target.get_snapshot_ref_by_name(name).unwrap();
        if source_snapshot.get_creation() != target_snapshot.get_creation() {
            return Err(EngineError::DatasetSnapshotCreationMismatchError);
        }
        Ok(
            SnapshotComparison::new(name.to_string(), source_snapshot.get_creation())
                .with_source(self.source.get_snapshot_position(name).unwrap())
                .with_target(self.target.get_snapshot_position(name).unwrap()),
        )
    }

    fn get_common_snapshot_names(&self) -> Vec<&str> {
        let source_names: HashSet<&str> = self.source.get_snapshot_names_iter().collect();
        let target_names: HashSet<&str> = self.target.get_snapshot_names_iter().collect();
        source_names.intersection(&target_names).copied().collect()
    }

    fn get_sequence_after(&self, name: &str) -> Vec<SnapshotComparison> {
        let mut sequence = Vec::new();
        self.source
            .get_snapshots_enumerated_after_name_iter(name)
            .for_each(|(position, snapshot)| {
                sequence.push(SnapshotComparison::from_source_snapshot(position, snapshot));
            });
        self.target
            .get_snapshots_enumerated_after_name_iter(name)
            .for_each(|(position, snapshot)| {
                sequence.push(SnapshotComparison::from_target_snapshot(position, snapshot));
            });
        sequence.sort_by_key(super::snapshot::SnapshotComparison::get_creation);
        sequence
    }

    fn get_sequence_before(&self, name: &str) -> Vec<SnapshotComparison> {
        let mut sequence = Vec::new();
        self.source
            .get_snapshots_enumerated_before_name_iter(name)
            .for_each(|(position, snapshot)| {
                sequence.push(SnapshotComparison::from_source_snapshot(position, snapshot));
            });
        self.target
            .get_snapshots_enumerated_before_name_iter(name)
            .for_each(|(position, snapshot)| {
                sequence.push(SnapshotComparison::from_target_snapshot(position, snapshot));
            });
        sequence.sort_by_key(super::snapshot::SnapshotComparison::get_creation);
        sequence
    }

    fn get_sequence_between(&self, start: &str, stop: &str) -> Vec<SnapshotComparison> {
        let mut sequence = Vec::new();
        self.source
            .get_snapshots_enumerated_between_names_iter(start, stop)
            .for_each(|(position, snapshot)| {
                sequence.push(SnapshotComparison::from_source_snapshot(position, snapshot));
            });
        self.target
            .get_snapshots_enumerated_between_names_iter(start, stop)
            .for_each(|(position, snapshot)| {
                sequence.push(SnapshotComparison::from_target_snapshot(position, snapshot));
            });
        sequence.sort_by_key(super::snapshot::SnapshotComparison::get_creation);
        sequence
    }

    fn sort_snapshot_names<'b>(names: Vec<&'b str>, dataset: &Dataset) -> Vec<&'b str> {
        let positions: Vec<usize> = dataset
            .get_snapshot_positions_iter(&names)
            .map(|position| position.unwrap())
            .collect();
        let mut merged: Vec<(&str, usize)> = names.into_iter().zip(positions).collect();
        merged.sort_by_key(|&(_, position)| position);
        merged.iter().map(|(name, _)| *name).collect()
    }
}

pub struct SequenceComparison {
    sequence: Vec<SnapshotComparison>,
}

impl SequenceComparison {
    pub fn from_datasets(source: &Dataset, target: &Dataset) -> Result<Self, EngineError> {
        Ok(Self {
            sequence: SequenceBuilder::from_datasets(source, target).build()?,
        })
    }

    fn common_positions_reversed_iter(&self) -> impl Iterator<Item = usize> {
        self.sequence
            .iter()
            .enumerate()
            .rev()
            .filter_map(|(position, entry)| {
                if entry.is_on_both() {
                    Some(position)
                } else {
                    None
                }
            })
    }

    pub fn free_iter(&self, overlap: i64) -> Result<impl Iterator<Item = &str>, EngineError> {
        if overlap == 0 {
            return Err(EngineError::OverlapZeroError);
        }
        let position = if overlap > 0 {
            self.common_positions_reversed_iter()
                .nth(usize::try_from(overlap - 1).map_err(EngineError::ArchUsizeError)?)
                .unwrap_or(0)
        } else {
            0 // negative values cause all snapshots to be kept
        };
        Ok(self.sequence[0..position].iter().filter_map(|entry| {
            if entry.is_on_source() {
                Some(entry.get_name_ref())
            } else {
                None
            }
        }))
    }

    pub fn sync_iter(&self) -> Result<impl Iterator<Item = (&str, &str)>, EngineError> {
        let start = if let Some(last_common) = self.get_last_common_position() {
            if !self.is_position_last_on_target(last_common) {
                return Err(EngineError::DatasetSnapshotAfterLastCommonError);
            }
            last_common
        } else {
            if !self.sequence.is_empty() {
                return Err(EngineError::DatasetSnapshotNoCommonError);
            }
            0 // HACK return empty iterator
        };
        Ok(self.sequence[start..]
            .iter()
            .zip(self.sequence.get(start + 1..).unwrap_or_default().iter())
            .map(|(a, b)| (a.get_name_ref(), b.get_name_ref())))
    }

    fn get_last_common_position(&self) -> Option<usize> {
        self.sequence
            .iter()
            .rev()
            .position(super::snapshot::SnapshotComparison::is_on_both)
            .map(|idx| self.sequence.len() - idx - 1)
    }

    fn is_position_last_on_target(&self, position: usize) -> bool {
        if position >= self.sequence.len() {
            return false;
        }
        if !self.sequence[position].is_on_target() {
            return false;
        }
        self.sequence[position + 1..]
            .iter()
            .all(|entry| !entry.is_on_target())
    }
}
