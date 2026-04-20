use crate::config::Location;
use crate::subprocess::Command;

use super::super::basebuilder::BaseBuilder;
use super::super::basemeta::BaseMeta;
use super::super::errors::TransactionBuildError;
use super::super::meta::TransactionMeta;
use super::super::transaction::Transaction;

#[derive(Clone)]
pub struct InventoryMeta {
    pub host: String,
    pub root: String,
}

impl InventoryMeta {
    #[must_use]
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

pub struct InventoryBuilder<'a> {
    location: &'a Location,
}

impl<'a> InventoryBuilder<'a> {
    #[must_use]
    pub const fn new(location: &'a Location) -> Self {
        Self { location }
    }
}

impl BaseBuilder for InventoryBuilder<'_> {
    fn build(self) -> Result<Transaction, TransactionBuildError> {
        Ok(Transaction::new(
            TransactionMeta::Inventory(InventoryMeta {
                host: self.location.get_route_ref().get_host_ref().to_string(),
                root: self.location.get_root_ref().to_string(),
            }),
            Command::new(
                "zfs".to_string(),
                vec![
                    "get".to_string(),
                    "-rHp".to_string(),
                    "all".to_string(),
                    self.location.get_root_ref().to_clean_string(),
                ],
            )
            .map_err(TransactionBuildError::Subprocess)?
            .on_route(self.location.get_route_ref())
            .map_err(TransactionBuildError::Subprocess)?,
            false,
        ))
    }
}
