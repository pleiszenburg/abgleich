use crate::config::Route;
use crate::subprocess::Command;

use super::super::basebuilder::BaseBuilder;
use super::super::basemeta::BaseMeta;
use super::super::errors::TransactionBuildError;
use super::super::meta::TransactionMeta;
use super::super::transaction::Transaction;

#[derive(Clone)]
pub struct WhichMeta {
    pub host: String,
    pub command: String,
}

impl BaseMeta for WhichMeta {
    fn to_description(&self, _color: bool, _si: bool) -> String {
        format!("which: {} ({})", self.command, self.host)
    }
}

pub struct WhichBuilder<'a> {
    route: &'a Route,
    command: String,
}

impl<'a> WhichBuilder<'a> {
    #[must_use]
    pub const fn new(
        route: &'a Route,
        command: String,
    ) -> Self {
        Self {
            route, command,
        }
    }
}

impl BaseBuilder for WhichBuilder<'_> {
    fn build(self) -> Result<Transaction, TransactionBuildError> {
        Ok(Transaction::new(
            TransactionMeta::Which(WhichMeta {
                host: self.route.get_host_ref().to_string(),
                command: self.command.clone(),
            }),
            Command::new("which".to_string(), vec![self.command])
                    .map_err(TransactionBuildError::Subprocess)?
                    .on_route(self.route)
                    .map_err(TransactionBuildError::Subprocess)?,
            false,
        ))
    }
}
