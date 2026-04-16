use crate::config::{InsecureHost, Location, Route, TransferOptions};
use crate::subprocess::{Command, CommandChain};

use super::super::basebuilder::BaseBuilder;
use super::super::basemeta::BaseMeta;
use super::super::errors::TransactionBuildError;
use super::super::meta::TransactionMeta;
use super::super::transaction::Transaction;

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

pub struct TransferInitialBuilder<'a> {
    source: &'a Location,
    target: &'a Location,
    dataset: String,
    snapshot: String,
    options: &'a TransferOptions,
}

impl<'a> TransferInitialBuilder<'a> {
    #[must_use]
    pub const fn new(
        source: &'a Location,
        target: &'a Location,
        dataset: String,
        snapshot: String,
        options: &'a TransferOptions,
    ) -> Self {
        Self {
            source, target, dataset, snapshot, options
        }
    }

    fn check_direct_route(route: &Route) -> Result<(), TransactionBuildError> {
        if route.has_consecutive_duplicates() {
            return Err(TransactionBuildError::DirectConsecutiveDuplicateHosts(
                route.to_string(),
            ));
        }
        Ok(())
    }

    fn insecure(self, insecure: &InsecureHost) -> Result<Transaction, TransactionBuildError> {
        let mut zfs_send_args = vec!["send".to_string()];
        if self.options.compress.is_none() {
            zfs_send_args.push("-c".to_string());
        }
        zfs_send_args.push(format!(
            "{}{}@{}",
            self.source.get_root_ref().as_str(),
            self.dataset,
            self.snapshot,
        ));
        let mut send_cmds =
            vec![Command::new("zfs".to_string(), zfs_send_args)
                .map_err(TransactionBuildError::Subprocess)?];
        if let Some(level) = self.options.compress {
            send_cmds.push(
                Command::new("xz".to_string(), vec![format!("-{level}")])
                    .map_err(TransactionBuildError::Subprocess)?,
            );
        }
        if let Some(rate) = self.options.rate_limit {
            send_cmds.push(
                Command::new(
                    "pv".to_string(),
                    vec!["-q".to_string(), "-L".to_string(), rate.to_string()],
                )
                .map_err(TransactionBuildError::Subprocess)?,
            );
        }
        send_cmds.push(
            Command::new("nc".to_string(), vec![insecure.hostname.clone(), insecure.port.to_string()])
                .map_err(TransactionBuildError::Subprocess)?,
        );
        let mut recv_cmds = vec![Command::new(
            "nc".to_string(),
            vec!["-l".to_string(), insecure.port.to_string()],
        )
        .map_err(TransactionBuildError::Subprocess)?];
        if self.options.compress.is_some() {
            recv_cmds.push(
                Command::new("xz".to_string(), vec!["-d".to_string()])
                    .map_err(TransactionBuildError::Subprocess)?,
            );
        }
        recv_cmds.push(
            Command::new(
                "zfs".to_string(),
                vec![
                    "receive".to_string(),
                    format!("{}{}", self.target.get_root_ref().as_str(), self.dataset),
                ],
            )
            .map_err(TransactionBuildError::Subprocess)?,
        );
        Ok(Transaction::new(
            TransactionMeta::TransferInitial(TransferInitialMeta {
                source_host: self.source.get_route_ref().get_host_ref().to_string(),
                target_host: self.target.get_route_ref().get_host_ref().to_string(),
                dataset: self.dataset,
                snapshot: self.snapshot,
            }),
            CommandChain::begin_group(self.source, send_cmds)
                .with_background_group(self.target, recv_cmds)
                .to_command()
                .map_err(TransactionBuildError::Subprocess)?,
            true,
        ))
    }

    fn secure(self) -> Result<Transaction, TransactionBuildError> {
        let (entry_route, source_relative, target_relative) = if self.options.direct {
            Self::check_direct_route(self.source.get_route_ref())?;
            Self::check_direct_route(self.target.get_route_ref())?;
            let (entry_route, source_route, target_route) =
                Route::split_common_prefix(self.source.get_route_ref(), self.target.get_route_ref());
            (entry_route, self.source.with_route(source_route), self.target.with_route(target_route))
        } else {
            (Route::from_localhost(None), self.source.clone(), self.target.clone())
        };
        let mut zfs_send_args = vec!["send".to_string()];
        if self.options.compress.is_none() {
            zfs_send_args.push("-c".to_string());
        }
        zfs_send_args.push(format!(
            "{}{}@{}",
            self.source.get_root_ref().as_str(),
            self.dataset,
            self.snapshot
        ));
        let mut src_cmds =
            vec![Command::new("zfs".to_string(), zfs_send_args)
                .map_err(TransactionBuildError::Subprocess)?];
        if let Some(level) = self.options.compress {
            src_cmds.push(
                Command::new("xz".to_string(), vec![format!("-{level}")])
                    .map_err(TransactionBuildError::Subprocess)?,
            );
        }
        if let Some(rate) = self.options.rate_limit {
            src_cmds.push(
                Command::new(
                    "pv".to_string(),
                    vec!["-q".to_string(), "-L".to_string(), rate.to_string()],
                )
                .map_err(TransactionBuildError::Subprocess)?,
            );
        }
        let mut tgt_cmds = Vec::new();
        if self.options.compress.is_some() {
            tgt_cmds.push(
                Command::new("xz".to_string(), vec!["-d".to_string()])
                    .map_err(TransactionBuildError::Subprocess)?,
            );
        }
        tgt_cmds.push(
            Command::new(
                "zfs".to_string(),
                vec![
                    "receive".to_string(),
                    format!("{}{}", self.target.get_root_ref().as_str(), self.dataset),
                ],
            )
            .map_err(TransactionBuildError::Subprocess)?,
        );
        Ok(Transaction::new(
            TransactionMeta::TransferInitial(TransferInitialMeta {
                source_host: self.source.get_route_ref().get_host_ref().to_string(),
                target_host: self.target.get_route_ref().get_host_ref().to_string(),
                dataset: self.dataset,
                snapshot: self.snapshot,
            }),
            CommandChain::begin_group(&source_relative, src_cmds)
                .pipe_group(&target_relative, tgt_cmds)
                .with_entry_route(entry_route)
                .map_err(TransactionBuildError::Subprocess)?
                .to_command()
                .map_err(TransactionBuildError::Subprocess)?,
            true,
        ))
    }
}

impl BaseBuilder for TransferInitialBuilder<'_> {
    fn build(self) -> Result<Transaction, TransactionBuildError> {
        // nc (insecure) path: receiver listens with nc, sender connects with nc.
        if let Some(insecure) = &self.options.insecure {
            return self.insecure(insecure);
        }
        // SSH pipe path (direct or default).
        self.secure()
    }
}
