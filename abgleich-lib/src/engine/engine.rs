use std::str::FromStr;

use colored::Colorize;
use serde_json::json;

use crate::config::{Config, Location, Route};
use crate::output::{Alignment, Table, TableColumn};
use crate::transaction::{Transaction, TransactionList, TransferOptions};

use super::apool::Apool;
use super::comparison::ApoolComparison;
use super::errors::EngineError;

pub struct Engine {
    config: Config,
}

impl Engine {
    pub fn from_detect() -> Result<Self, EngineError> {
        let config = Config::from_detect().map_err(EngineError::ConfigError)?;
        Ok(Self { config })
    }

    #[cfg(feature = "cli")]
    pub fn free_cli(
        &self,
        json: bool,
        yes: bool,
        force: bool,
        source: &str,
        target: &str,
    ) -> Result<(), EngineError> {
        let source_loc =
            self.config.parse_location(source).map_err(EngineError::ConfigError)?;
        let target_loc =
            self.config.parse_location(target).map_err(EngineError::ConfigError)?;
        for (loc, err) in [
            (&source_loc, EngineError::ZfsCommandNotFound {
                host: source_loc.get_route_ref().get_host_ref().to_string(),
            }),
            (&target_loc, EngineError::ZfsCommandNotFound {
                host: target_loc.get_route_ref().get_host_ref().to_string(),
            }),
        ] {
            if !Transaction::new_which(loc.get_route_ref(), "zfs".to_string())
                .map_err(EngineError::TransactionError)?
                .run()
                .map_err(EngineError::TransactionError)?
                .is_successful()
            {
                return Err(err);
            }
        }
        let transactions = self.get_free_transactions(source, target)?;
        transactions
            .run_cli(json, yes, force)
            .map_err(EngineError::TransactionError)
    }

    pub fn get_free_transactions(
        &self,
        source: &str,
        target: &str,
    ) -> Result<TransactionList, EngineError> {
        let source = self
            .config
            .parse_location(source)
            .map_err(EngineError::ConfigError)?;
        let target = self
            .config
            .parse_location(target)
            .map_err(EngineError::ConfigError)?;
        let source_apool = Apool::from_location(source)?;
        let target_apool = Apool::from_location(target)?;
        ApoolComparison::new(&source_apool, &target_apool).get_free_transactions()
    }

    pub fn get_snap_transactions(&self, location: &str) -> Result<TransactionList, EngineError> {
        let location = self
            .config
            .parse_location(location)
            .map_err(EngineError::ConfigError)?;
        let apool = Apool::from_location(location)?;
        apool.get_create_snapshot_transactions()
    }

    pub fn get_sync_transactions(
        &self,
        source: &str,
        target: &str,
        direct: bool,
        options: &TransferOptions,
    ) -> Result<TransactionList, EngineError> {
        let source = self
            .config
            .parse_location(source)
            .map_err(EngineError::ConfigError)?;
        let target = self
            .config
            .parse_location(target)
            .map_err(EngineError::ConfigError)?;
        let source_apool = Apool::from_location(source)?;
        let target_apool = Apool::from_location(target)?;
        ApoolComparison::new(&source_apool, &target_apool).get_sync_transactions(direct, options)
    }

    fn get_zpools(route: &Route) -> Result<Vec<Location>, EngineError> {
        let zpool_list = Transaction::new_zpool_list(route)
            .map_err(EngineError::TransactionError)?
            .run()
            .map_err(EngineError::TransactionError)?;
        zpool_list
            .assert_success()
            .map_err(EngineError::TransactionError)?;
        let raw = zpool_list.get_data_ref().unwrap(); // safe operation
        let lines = raw.split('\n');
        let chars: &[_] = &[' ', '\t'];
        let mut locations: Vec<Location> = Vec::new();
        for line in lines {
            let line_cleaned = line.trim_matches(chars);
            if line_cleaned.is_empty() {
                continue;
            }
            let fragments: Vec<&str> = line.split('\t').collect();
            let location = format!("{}:{}", route.to_string(), fragments[0]);
            locations.push(Location::from_str(&location).map_err(EngineError::ConfigError)?);
        }
        Ok(locations)
    }

    #[cfg(feature = "cli")]
    pub fn ls_cli(&self, json: bool, location: Option<&str>) -> Result<(), EngineError> {
        if let Some(location) = location {
            if let Some(clean_location) = location.strip_suffix(':') {
                let route = Route::from_str(clean_location).map_err(EngineError::ConfigError)?;
                if json {
                    self.print_json(&route)
                } else {
                    self.print_table(&route)
                }
            } else {
                let location = self
                    .config
                    .parse_location(location)
                    .map_err(EngineError::ConfigError)?;
                if !Transaction::new_which(location.get_route_ref(), "zfs".to_string())
                    .map_err(EngineError::TransactionError)?
                    .run()
                    .map_err(EngineError::TransactionError)?
                    .is_successful()
                {
                    return Err(EngineError::ZfsCommandNotFound {
                        host: location.get_route_ref().get_host_ref().to_string(),
                    });
                }
                let apool = Apool::from_location(location)?;
                if json {
                    apool.print_json()
                } else {
                    apool.print_table()
                }
            }
        } else {
            let route = Route::from_localhost();
            if json {
                self.print_json(&route)
            } else {
                self.print_table(&route)
            }
        }
    }

    pub fn print_json(&self, route: &Route) -> Result<(), EngineError> {
        if *route == Route::from_localhost() {
            for (alias, location) in self.config.get_apools_iter() {
                println!(
                    "{}",
                    json!({
                        "alias": alias.to_owned(),
                        "route": location.get_route_ref().to_string(),
                        "user": location.get_user_ref(),
                        "root": location.get_root_ref().to_string(),
                    })
                );
            }
        }
        if !Transaction::new_which(route, "zpool".to_string())
            .map_err(EngineError::TransactionError)?
            .run()
            .map_err(EngineError::TransactionError)?
            .is_successful()
        {
            return Err(EngineError::ZpoolCommandNotFound);
        }
        for location in Self::get_zpools(route)? {
            if !self.config.contains(&location) {
                println!(
                    "{}",
                    json!({
                        "alias": None::<String>,
                        "route": location.get_route_ref().to_string(),
                        "user": location.get_user_ref(),
                        "root": location.get_root_ref().to_string(),
                    })
                );
            }
        }
        Ok(())
    }

    pub fn print_table(&self, route: &Route) -> Result<(), EngineError> {
        let mut table = Table::new(vec![
            TableColumn::new("alias".to_string(), Alignment::Left),
            TableColumn::new("route".to_string(), Alignment::Left),
            TableColumn::new("user".to_string(), Alignment::Left),
            TableColumn::new("root".to_string(), Alignment::Left),
        ]);
        if *route == Route::from_localhost() {
            for (alias, location) in self.config.get_apools_iter() {
                table.push_row(vec![
                    alias.green().to_string(),
                    location.get_route_ref().to_string().green().to_string(),
                    location.get_user_ref().unwrap_or(" ").green().to_string(),
                    location.get_root_ref().to_string().green().to_string(),
                ]);
            }
        }
        if !Transaction::new_which(route, "zpool".to_string())
            .map_err(EngineError::TransactionError)?
            .run()
            .map_err(EngineError::TransactionError)?
            .is_successful()
        {
            return Err(EngineError::ZpoolCommandNotFound);
        }
        for location in Self::get_zpools(route)? {
            if !self.config.contains(&location) {
                table.push_row(vec![
                    " ".to_string(),
                    location.get_route_ref().to_string(),
                    location.get_user_ref().unwrap_or(" ").to_owned(),
                    location.get_root_ref().to_string(),
                ]);
            }
        }
        table.print();
        Ok(())
    }

    #[cfg(feature = "cli")]
    pub fn snap_cli(&self, json: bool, yes: bool, force: bool, location: &str) -> Result<(), EngineError> {
        let loc = self.config.parse_location(location).map_err(EngineError::ConfigError)?;
        if !Transaction::new_which(loc.get_route_ref(), "zfs".to_string())
            .map_err(EngineError::TransactionError)?
            .run()
            .map_err(EngineError::TransactionError)?
            .is_successful()
        {
            return Err(EngineError::ZfsCommandNotFound {
                host: loc.get_route_ref().get_host_ref().to_string(),
            });
        }
        let transactions = self.get_snap_transactions(location)?;
        transactions
            .run_cli(json, yes, force)
            .map_err(EngineError::TransactionError)
    }

    #[cfg(feature = "cli")]
    pub fn sync_cli(
        &self,
        json: bool,
        yes: bool,
        direct: bool,
        force: bool,
        rate_limit: Option<u64>,
        compress: Option<u8>,
        insecure: Option<(String, u16)>,
        source: &str,
        target: &str,
    ) -> Result<(), EngineError> {
        if direct && insecure.is_some() {
            return Err(EngineError::DirectAndInsecureConflict);
        }
        let source_loc =
            self.config.parse_location(source).map_err(EngineError::ConfigError)?;
        let target_loc =
            self.config.parse_location(target).map_err(EngineError::ConfigError)?;
        for (loc, err) in [
            (&source_loc, EngineError::ZfsCommandNotFound {
                host: source_loc.get_route_ref().get_host_ref().to_string(),
            }),
            (&target_loc, EngineError::ZfsCommandNotFound {
                host: target_loc.get_route_ref().get_host_ref().to_string(),
            }),
        ] {
            if !Transaction::new_which(loc.get_route_ref(), "zfs".to_string())
                .map_err(EngineError::TransactionError)?
                .run()
                .map_err(EngineError::TransactionError)?
                .is_successful()
            {
                return Err(err);
            }
        }
        if rate_limit.is_some()
            && !Transaction::new_which(source_loc.get_route_ref(), "pv".to_string())
                .map_err(EngineError::TransactionError)?
                .run()
                .map_err(EngineError::TransactionError)?
                .is_successful()
            {
                return Err(EngineError::PvCommandNotFound {
                    host: source_loc.get_route_ref().get_host_ref().to_string(),
                });
            }
        if compress.is_some() {
            for (loc, err) in [
                (&source_loc, EngineError::XzCommandNotFound {
                    host: source_loc.get_route_ref().get_host_ref().to_string(),
                }),
                (&target_loc, EngineError::XzCommandNotFound {
                    host: target_loc.get_route_ref().get_host_ref().to_string(),
                }),
            ] {
                if !Transaction::new_which(loc.get_route_ref(), "xz".to_string())
                    .map_err(EngineError::TransactionError)?
                    .run()
                    .map_err(EngineError::TransactionError)?
                    .is_successful()
                {
                    return Err(err);
                }
            }
        }
        if insecure.is_some() {
            for (loc, err) in [
                (&source_loc, EngineError::NcCommandNotFound {
                    host: source_loc.get_route_ref().get_host_ref().to_string(),
                }),
                (&target_loc, EngineError::NcCommandNotFound {
                    host: target_loc.get_route_ref().get_host_ref().to_string(),
                }),
            ] {
                if !Transaction::new_which(loc.get_route_ref(), "nc".to_string())
                    .map_err(EngineError::TransactionError)?
                    .run()
                    .map_err(EngineError::TransactionError)?
                    .is_successful()
                {
                    return Err(err);
                }
            }
        }
        let options = TransferOptions { rate_limit, compress, insecure };
        let transactions = self.get_sync_transactions(source, target, direct, &options)?;
        transactions
            .run_cli(json, yes, force)
            .map_err(EngineError::TransactionError)
    }
}
