use tracing::info;

use crate::config::{Location, Route};
use crate::subprocess::{Command, CommandChain};
use crate::transaction::meta::{DiffMeta, TransferInitialMeta};

use super::errors::TransactionError;
use super::meta::{
    CreateSnapshotMeta, DestroySnapshotMeta, InventoryMeta, TransactionMeta,
    TransferIncrementalMeta, Which, ZpoolList,
};
use super::options::TransferOptions;
use super::outcome::TransactionOutcome;

fn check_direct_route(route: &Route) -> Result<(), TransactionError> {
    if route.has_consecutive_duplicates() {
        return Err(TransactionError::DirectConsecutiveDuplicateHostsError(
            route.to_string(),
        ));
    }
    Ok(())
}

pub struct TransactionJsonFields {
    pub description: String,
    pub chain: String,
}

pub struct TransactionTableRow {
    pub description: String,
    pub chain: String,
}

pub struct Transaction {
    meta: TransactionMeta,
    chain: CommandChain,
}

impl Transaction {
    pub fn to_json_row(&self) -> Result<TransactionJsonFields, TransactionError> {
        Ok(TransactionJsonFields {
            description: self.meta.to_description(false, false),
            chain: self.chain.to_string(),
        })
    }

    pub fn to_table_row(&self) -> Result<TransactionTableRow, TransactionError> {
        Ok(TransactionTableRow {
            description: self.meta.to_description(true, true),
            chain: self.chain.to_string(),
        })
    }

    pub fn run(&self) -> Result<TransactionOutcome, TransactionError> {
        info!(
            message = format!("[RUN] {}", self.meta.to_description(false, false)),
            command = self.chain.to_string(),
        );
        let outcome = self
            .chain
            .run()
            .map_err(TransactionError::SubprocessError)?;
        let success = outcome.success();
        if success {
            info!("[OK] {}", self.meta.to_description(false, false));
        } else {
            info!("[FAILED] {}", self.meta.to_description(false, false));
        }
        let data = outcome
            .stdout_as_str_ref()
            .map_err(TransactionError::SubprocessError)?
            .to_string();
        let data = match &self.meta {
            TransactionMeta::Inventory(meta) => meta.handle_root_output(data),
            _ => data,
        };
        Ok(TransactionOutcome::new(
            success,
            Some(data),
            self.meta.clone(),
        ))
    }

    pub fn new_create_snapshot(
        location: &Location,
        dataset: String,
        snapshot: String,
        written: u64,
    ) -> Result<Self, TransactionError> {
        let dataset_name = if dataset == "/" { "" } else { &dataset };
        Ok(Self {
            chain: CommandChain::begin(
                Command::new(
                    "zfs".to_string(),
                    vec![
                        "snapshot".to_string(),
                        format!(
                            "{}{}@{}",
                            location.get_root_ref().as_str(),
                            dataset_name,
                            snapshot
                        ),
                    ],
                )
                .map_err(TransactionError::SubprocessError)?
                .on_location(location)
                .map_err(TransactionError::SubprocessError)?,
            ),
            meta: TransactionMeta::CreateSnapshot(CreateSnapshotMeta {
                host: location.get_route_ref().get_host_ref().to_string(),
                written,
                dataset,
                snapshot,
            }),
        })
    }

    pub fn new_destroy_snapshot(
        location: &Location,
        dataset: String,
        snapshot: String,
    ) -> Result<Self, TransactionError> {
        let dataset_name = if dataset == "/" { "" } else { &dataset };
        Ok(Self {
            chain: CommandChain::begin(
                Command::new(
                    "zfs".to_string(),
                    vec![
                        "destroy".to_string(),
                        format!(
                            "{}{}@{}",
                            location.get_root_ref().as_str(),
                            dataset_name,
                            snapshot
                        ),
                    ],
                )
                .map_err(TransactionError::SubprocessError)?
                .on_location(location)
                .map_err(TransactionError::SubprocessError)?,
            ),
            meta: TransactionMeta::DestroySnapshot(DestroySnapshotMeta {
                host: location.get_route_ref().get_host_ref().to_string(),
                dataset,
                snapshot,
            }),
        })
    }

    pub fn new_diff(
        location: &Location,
        dataset: String,
        snapshot: String,
    ) -> Result<Self, TransactionError> {
        let dataset_name = if dataset == "/" { "" } else { &dataset };
        Ok(Self {
            chain: CommandChain::begin(
                Command::new(
                    "zfs".to_string(),
                    vec![
                        "diff".to_string(),
                        format!(
                            "{}{}@{}",
                            location.get_root_ref().as_str(),
                            dataset_name,
                            snapshot,
                        ),
                    ],
                )
                .map_err(TransactionError::SubprocessError)?
                .on_location(location)
                .map_err(TransactionError::SubprocessError)?,
            ),
            meta: TransactionMeta::Diff(DiffMeta {
                host: location.get_route_ref().get_host_ref().to_string(),
                dataset,
                snapshot,
            }),
        })
    }

    pub fn new_inventory(location: &Location) -> Result<Self, TransactionError> {
        Ok(Self {
            chain: CommandChain::begin(
                Command::new(
                    "zfs".to_string(),
                    vec![
                        "get".to_string(),
                        "-rHp".to_string(),
                        "all".to_string(),
                        location.get_root_ref().to_clean_string(),
                    ],
                )
                .map_err(TransactionError::SubprocessError)?
                .on_location(location)
                .map_err(TransactionError::SubprocessError)?,
            ),
            meta: TransactionMeta::Inventory(InventoryMeta {
                host: location.get_route_ref().get_host_ref().to_string(),
                root: location.get_root_ref().to_string(),
            }),
        })
    }

    pub fn new_transfer_incremental(
        source: &Location,
        target: &Location,
        dataset: String,
        from_snapshot: String,
        to_snapshot: String,
        direct: bool,
        options: &TransferOptions,
    ) -> Result<Self, TransactionError> {
        // nc (insecure) path: receiver listens with nc, sender connects with nc.
        if let Some((nc_host, nc_port)) = &options.insecure {
            let mut zfs_send_args = vec!["send".to_string()];
            if options.compress.is_none() {
                zfs_send_args.push("-c".to_string());
            }
            zfs_send_args.extend([
                "-i".to_string(),
                format!("{}{}@{}", source.get_root_ref().as_str(), dataset, from_snapshot),
                format!("{}{}@{}", source.get_root_ref().as_str(), dataset, to_snapshot),
            ]);
            let mut send_cmds =
                vec![Command::new("zfs".to_string(), zfs_send_args)
                    .map_err(TransactionError::SubprocessError)?];
            if let Some(level) = options.compress {
                send_cmds.push(
                    Command::new("xz".to_string(), vec![format!("-{level}")])
                        .map_err(TransactionError::SubprocessError)?,
                );
            }
            if let Some(rate) = options.rate_limit {
                send_cmds.push(
                    Command::new(
                        "pv".to_string(),
                        vec!["-q".to_string(), "-L".to_string(), rate.to_string()],
                    )
                    .map_err(TransactionError::SubprocessError)?,
                );
            }
            send_cmds.push(
                Command::new("nc".to_string(), vec![nc_host.clone(), nc_port.to_string()])
                    .map_err(TransactionError::SubprocessError)?,
            );

            let mut recv_cmds = vec![Command::new(
                "nc".to_string(),
                vec!["-l".to_string(), nc_port.to_string()],
            )
            .map_err(TransactionError::SubprocessError)?];
            if options.compress.is_some() {
                recv_cmds.push(
                    Command::new("xz".to_string(), vec!["-d".to_string()])
                        .map_err(TransactionError::SubprocessError)?,
                );
            }
            recv_cmds.push(
                Command::new(
                    "zfs".to_string(),
                    vec![
                        "receive".to_string(),
                        format!("{}{}", target.get_root_ref().as_str(), dataset),
                    ],
                )
                .map_err(TransactionError::SubprocessError)?,
            );

            return Ok(Self {
                chain: CommandChain::begin_group(source, send_cmds)
                    .with_background_group(target, recv_cmds),
                meta: TransactionMeta::TransferIncremental(TransferIncrementalMeta {
                    source_host: source.get_route_ref().get_host_ref().to_string(),
                    target_host: target.get_route_ref().get_host_ref().to_string(),
                    dataset,
                    from_snapshot,
                    to_snapshot,
                }),
            });
        }

        // SSH pipe path (direct or default).
        let (entry_route, source_relative, target_relative) = if direct {
            check_direct_route(source.get_route_ref())?;
            check_direct_route(target.get_route_ref())?;
            let (entry_route, source_route, target_route) =
                Route::split_common_prefix(source.get_route_ref(), target.get_route_ref());
            (entry_route, source.with_route(source_route), target.with_route(target_route))
        } else {
            (Route::from_localhost(), source.clone(), target.clone())
        };

        let mut zfs_send_args = vec!["send".to_string()];
        // -c (send compressed blocks) is mutually exclusive with xz: feeding
        // already-compressed data into xz degrades its efficiency.
        if options.compress.is_none() {
            zfs_send_args.push("-c".to_string());
        }
        zfs_send_args.extend([
            "-i".to_string(),
            format!("{}{}@{}", source.get_root_ref().as_str(), dataset, from_snapshot),
            format!("{}{}@{}", source.get_root_ref().as_str(), dataset, to_snapshot),
        ]);
        let mut src_cmds =
            vec![Command::new("zfs".to_string(), zfs_send_args)
                .map_err(TransactionError::SubprocessError)?];
        if let Some(level) = options.compress {
            src_cmds.push(
                Command::new("xz".to_string(), vec![format!("-{level}")])
                    .map_err(TransactionError::SubprocessError)?,
            );
        }
        if let Some(rate) = options.rate_limit {
            src_cmds.push(
                Command::new(
                    "pv".to_string(),
                    vec!["-q".to_string(), "-L".to_string(), rate.to_string()],
                )
                .map_err(TransactionError::SubprocessError)?,
            );
        }
        let mut tgt_cmds = Vec::new();
        if options.compress.is_some() {
            tgt_cmds.push(
                Command::new("xz".to_string(), vec!["-d".to_string()])
                    .map_err(TransactionError::SubprocessError)?,
            );
        }
        tgt_cmds.push(
            Command::new(
                "zfs".to_string(),
                vec![
                    "receive".to_string(),
                    format!("{}{}", target.get_root_ref().as_str(), dataset),
                ],
            )
            .map_err(TransactionError::SubprocessError)?,
        );

        Ok(Self {
            chain: CommandChain::begin_group(&source_relative, src_cmds)
                .pipe_group(&target_relative, tgt_cmds)
                .with_entry_route(entry_route),
            meta: TransactionMeta::TransferIncremental(TransferIncrementalMeta {
                source_host: source.get_route_ref().get_host_ref().to_string(),
                target_host: target.get_route_ref().get_host_ref().to_string(),
                dataset,
                from_snapshot,
                to_snapshot,
            }),
        })
    }

    pub fn new_transfer_initial(
        source: &Location,
        target: &Location,
        dataset: String,
        snapshot: String,
        direct: bool,
        options: &TransferOptions,
    ) -> Result<Self, TransactionError> {
        // nc (insecure) path: receiver listens with nc, sender connects with nc.
        if let Some((nc_host, nc_port)) = &options.insecure {
            let mut zfs_send_args = vec!["send".to_string()];
            if options.compress.is_none() {
                zfs_send_args.push("-c".to_string());
            }
            zfs_send_args.push(format!(
                "{}{}@{}",
                source.get_root_ref().as_str(),
                dataset,
                snapshot,
            ));
            let mut send_cmds =
                vec![Command::new("zfs".to_string(), zfs_send_args)
                    .map_err(TransactionError::SubprocessError)?];
            if let Some(level) = options.compress {
                send_cmds.push(
                    Command::new("xz".to_string(), vec![format!("-{level}")])
                        .map_err(TransactionError::SubprocessError)?,
                );
            }
            if let Some(rate) = options.rate_limit {
                send_cmds.push(
                    Command::new(
                        "pv".to_string(),
                        vec!["-q".to_string(), "-L".to_string(), rate.to_string()],
                    )
                    .map_err(TransactionError::SubprocessError)?,
                );
            }
            send_cmds.push(
                Command::new("nc".to_string(), vec![nc_host.clone(), nc_port.to_string()])
                    .map_err(TransactionError::SubprocessError)?,
            );

            let mut recv_cmds = vec![Command::new(
                "nc".to_string(),
                vec!["-l".to_string(), nc_port.to_string()],
            )
            .map_err(TransactionError::SubprocessError)?];
            if options.compress.is_some() {
                recv_cmds.push(
                    Command::new("xz".to_string(), vec!["-d".to_string()])
                        .map_err(TransactionError::SubprocessError)?,
                );
            }
            recv_cmds.push(
                Command::new(
                    "zfs".to_string(),
                    vec![
                        "receive".to_string(),
                        format!("{}{}", target.get_root_ref().as_str(), dataset),
                    ],
                )
                .map_err(TransactionError::SubprocessError)?,
            );

            return Ok(Self {
                chain: CommandChain::begin_group(source, send_cmds)
                    .with_background_group(target, recv_cmds),
                meta: TransactionMeta::TransferInitial(TransferInitialMeta {
                    source_host: source.get_route_ref().get_host_ref().to_string(),
                    target_host: target.get_route_ref().get_host_ref().to_string(),
                    dataset,
                    snapshot,
                }),
            });
        }

        // SSH pipe path (direct or default).
        let (entry_route, source_relative, target_relative) = if direct {
            check_direct_route(source.get_route_ref())?;
            check_direct_route(target.get_route_ref())?;
            let (entry_route, source_route, target_route) =
                Route::split_common_prefix(source.get_route_ref(), target.get_route_ref());
            (entry_route, source.with_route(source_route), target.with_route(target_route))
        } else {
            (Route::from_localhost(), source.clone(), target.clone())
        };

        let mut zfs_send_args = vec!["send".to_string()];
        if options.compress.is_none() {
            zfs_send_args.push("-c".to_string());
        }
        zfs_send_args.push(format!(
            "{}{}@{}",
            source.get_root_ref().as_str(),
            dataset,
            snapshot
        ));
        let mut src_cmds =
            vec![Command::new("zfs".to_string(), zfs_send_args)
                .map_err(TransactionError::SubprocessError)?];
        if let Some(level) = options.compress {
            src_cmds.push(
                Command::new("xz".to_string(), vec![format!("-{level}")])
                    .map_err(TransactionError::SubprocessError)?,
            );
        }
        if let Some(rate) = options.rate_limit {
            src_cmds.push(
                Command::new(
                    "pv".to_string(),
                    vec!["-q".to_string(), "-L".to_string(), rate.to_string()],
                )
                .map_err(TransactionError::SubprocessError)?,
            );
        }
        let mut tgt_cmds = Vec::new();
        if options.compress.is_some() {
            tgt_cmds.push(
                Command::new("xz".to_string(), vec!["-d".to_string()])
                    .map_err(TransactionError::SubprocessError)?,
            );
        }
        tgt_cmds.push(
            Command::new(
                "zfs".to_string(),
                vec![
                    "receive".to_string(),
                    format!("{}{}", target.get_root_ref().as_str(), dataset),
                ],
            )
            .map_err(TransactionError::SubprocessError)?,
        );

        Ok(Self {
            chain: CommandChain::begin_group(&source_relative, src_cmds)
                .pipe_group(&target_relative, tgt_cmds)
                .with_entry_route(entry_route),
            meta: TransactionMeta::TransferInitial(TransferInitialMeta {
                source_host: source.get_route_ref().get_host_ref().to_string(),
                target_host: target.get_route_ref().get_host_ref().to_string(),
                dataset,
                snapshot,
            }),
        })
    }

    pub fn new_which(route: &Route, command: String) -> Result<Self, TransactionError> {
        Ok(Self {
            chain: CommandChain::begin(
                Command::new("which".to_string(), vec![command.clone()])
                    .map_err(TransactionError::SubprocessError)?
                    .on_route(route)
                    .map_err(TransactionError::SubprocessError)?,
            ),
            meta: TransactionMeta::Which(Which {
                host: route.get_host_ref().to_string(),
                command,
            }),
        })
    }

    pub fn new_zpool_list(route: &Route) -> Result<Self, TransactionError> {
        Ok(Self {
            chain: CommandChain::begin(
                Command::new(
                    "zpool".to_string(),
                    vec!["list".to_string(), "-Hp".to_string()],
                )
                .map_err(TransactionError::SubprocessError)?
                .on_route(route)
                .map_err(TransactionError::SubprocessError)?,
            ),
            meta: TransactionMeta::ZpoolList(ZpoolList {
                host: route.get_host_ref().to_string(),
            }),
        })
    }
}
