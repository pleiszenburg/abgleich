use crate::output::{colorized_storage_si_suffix, storage_si_suffix, storage_suffix};

trait BaseMeta {
    fn to_description(&self, color: bool, si: bool) -> String;
}

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

#[derive(Clone)]
pub struct DiffMeta {
    pub host: String,
    pub dataset: String,
    pub snapshot: String,
}

impl BaseMeta for DiffMeta {
    fn to_description(&self, _color: bool, _si: bool) -> String {
        format!("diff: {}:{}@{}", self.host, self.dataset, self.snapshot)
    }
}

#[derive(Clone)]
pub struct InventoryMeta {
    pub host: String,
    pub root: String,
}

impl InventoryMeta {
    pub fn handle_root_output(&self, data: String) -> String {
        if !self.root.ends_with('/') {
            return data;
        }
        let pattern = format!("{}\t", &self.root[..self.root.len() - 1]);
        let lines: Vec<&str> = data
            .split('\n')
            .filter(|line| !line.starts_with(&pattern))
            .collect();
        lines.join("\n")
    }
}

impl BaseMeta for InventoryMeta {
    fn to_description(&self, _color: bool, _si: bool) -> String {
        format!("inventory: {}:{}", self.host, self.root)
    }
}

#[derive(Clone)]
pub struct TransferIncrementalMeta {
    pub source_host: String,
    pub target_host: String,
    pub dataset: String,
    pub from_snapshot: String,
    pub to_snapshot: String,
}

impl BaseMeta for TransferIncrementalMeta {
    fn to_description(&self, _color: bool, _si: bool) -> String {
        format!(
            "transfer followup: {}:{}@{}..{}->{}",
            self.source_host, self.dataset, self.from_snapshot, self.to_snapshot, self.target_host,
        )
    }
}

#[derive(Clone)]
pub struct TransferInitialMeta {
    pub source_host: String,
    pub target_host: String,
    pub dataset: String,
    pub snapshot: String,
}

impl BaseMeta for TransferInitialMeta {
    fn to_description(&self, _color: bool, _si: bool) -> String {
        format!(
            "transfer initial: {}:{}@{}->{}",
            self.source_host, self.dataset, self.snapshot, self.target_host,
        )
    }
}

#[derive(Clone)]
pub struct Which {
    pub host: String,
    pub command: String,
}

impl BaseMeta for Which {
    fn to_description(&self, _color: bool, _si: bool) -> String {
        format!("which: {} ({})", self.command, self.host)
    }
}

#[derive(Clone)]
pub struct ZpoolList {
    pub host: String,
}

impl BaseMeta for ZpoolList {
    fn to_description(&self, _color: bool, _si: bool) -> String {
        format!("zpool: list ({})", self.host)
    }
}

#[derive(Clone)]
pub enum TransactionMeta {
    CreateSnapshot(CreateSnapshotMeta),
    DestroySnapshot(DestroySnapshotMeta),
    Diff(DiffMeta),
    Inventory(InventoryMeta),
    TransferIncremental(TransferIncrementalMeta),
    TransferInitial(TransferInitialMeta),
    Which(Which),
    ZpoolList(ZpoolList),
}

impl TransactionMeta {
    pub fn to_description(&self, color: bool, si: bool) -> String {
        match self {
            Self::CreateSnapshot(meta) => meta.to_description(color, si),
            Self::DestroySnapshot(meta) => meta.to_description(color, si),
            Self::Diff(meta) => meta.to_description(color, si),
            Self::Inventory(meta) => meta.to_description(color, si),
            Self::TransferIncremental(meta) => meta.to_description(color, si),
            Self::TransferInitial(meta) => meta.to_description(color, si),
            Self::Which(meta) => meta.to_description(color, si),
            Self::ZpoolList(meta) => meta.to_description(color, si),
        }
    }
}
