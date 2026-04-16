use super::basemeta::BaseMeta;
use super::variants::{
    CreateSnapshotMeta,
    DestroySnapshotMeta,
    DiffMeta,
    InventoryMeta,
    TransferIncrementalMeta,
    TransferInitialMeta,
    WhichMeta,
    ZpoolListMeta,
};

#[derive(Clone)]
pub enum TransactionMeta {
    CreateSnapshot(CreateSnapshotMeta),
    DestroySnapshot(DestroySnapshotMeta),
    Diff(DiffMeta),
    Inventory(InventoryMeta),
    TransferIncremental(TransferIncrementalMeta),
    TransferInitial(TransferInitialMeta),
    Which(WhichMeta),
    ZpoolList(ZpoolListMeta),
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
