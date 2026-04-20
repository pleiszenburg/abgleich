use crate::config::Route;
use crate::subprocess::Command;

use super::super::basebuilder::BaseBuilder;
use super::super::basemeta::BaseMeta;
use super::super::errors::TransactionBuildError;
use super::super::meta::TransactionMeta;
use super::super::transaction::Transaction;

#[derive(Clone)]
pub struct ZpoolListMeta {
    pub host: String,
}

impl BaseMeta for ZpoolListMeta {
    fn to_description(&self, _color: bool, _si: bool) -> String {
        format!("zpool: list ({})", self.host)
    }
}

pub struct ZpoolListBuilder<'a> {
    route: &'a Route,
}

impl<'a> ZpoolListBuilder<'a> {
    #[must_use]
    pub const fn new(route: &'a Route) -> Self {
        Self { route }
    }
}

impl BaseBuilder for ZpoolListBuilder<'_> {
    fn build(self) -> Result<Transaction, TransactionBuildError> {
        Ok(Transaction::new(
            TransactionMeta::ZpoolList(ZpoolListMeta {
                host: self.route.get_host_ref().to_string(),
            }),
            Command::new(
                "zpool".to_string(),
                vec!["list".to_string(), "-Hp".to_string()],
            )
            .map_err(TransactionBuildError::Subprocess)?
            .on_route(self.route)
            .map_err(TransactionBuildError::Subprocess)?,
            false,
        ))
    }
}
