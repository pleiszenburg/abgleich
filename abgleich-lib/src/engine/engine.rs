use colored::Colorize;
use serde_json::json;

use crate::config::{Config, Location, Root, Route, TransferOptions};
#[cfg(feature = "cli")]
use crate::config::{Confirmation, OutputFmt};
use crate::output::{Alignment, Table, TableColumn};
#[cfg(feature = "cli")]
use crate::transaction::Force;
use crate::transaction::{BaseBuilder, TransactionList, WhichBuilder, ZpoolListBuilder};

use super::apool::Apool;
use super::comparison::ApoolComparison;
use super::errors::EngineError;

pub struct Engine {
    config: Config,
}

impl Engine {
    fn assert_command(route: &Route, command: String) -> Result<(), EngineError> {
        if !WhichBuilder::new(route, command.clone())
            .build()
            .map_err(EngineError::TransactionBuild)?
            .run()
            .map_err(EngineError::TransactionRun)?
            .is_successful()
        {
            return Err(EngineError::CommandNotFound {
                host: route.get_host_ref().to_string(),
                user: route.get_user_ref().unwrap_or("[default]").to_string(),
                command,
            });
        }
        Ok(())
    }

    pub fn from_detect() -> Result<Self, EngineError> {
        let config = Config::from_detect().map_err(EngineError::Config)?;
        Ok(Self { config })
    }

    #[cfg(feature = "cli")]
    pub fn free_cli(
        &self,
        outputfmt: &OutputFmt,
        confirmation: &Confirmation,
        force: bool,
        source: &str,
        target: &str,
    ) -> Result<(), EngineError> {
        let force = Force::from_bool(force).map_err(EngineError::TransactionBuild)?;
        let source_loc = self
            .config
            .parse_location(source)
            .map_err(EngineError::Config)?;
        let target_loc = self
            .config
            .parse_location(target)
            .map_err(EngineError::Config)?;
        Self::assert_command(source_loc.get_route_ref(), "zfs".to_string())?;
        Self::assert_command(target_loc.get_route_ref(), "zfs".to_string())?;
        let transactions = self.get_free_transactions(source, target)?;
        transactions
            .run_cli(outputfmt, confirmation, &force)
            .map_err(EngineError::TransactionCli)
    }

    pub fn get_free_transactions(
        &self,
        source: &str,
        target: &str,
    ) -> Result<TransactionList, EngineError> {
        let source = self
            .config
            .parse_location(source)
            .map_err(EngineError::Config)?;
        let target = self
            .config
            .parse_location(target)
            .map_err(EngineError::Config)?;
        let source_apool = Apool::from_location(source)?;
        let target_apool = Apool::from_location(target)?;
        ApoolComparison::new(&source_apool, &target_apool).get_free_transactions()
    }

    pub fn get_snap_transactions(&self, location: &str) -> Result<TransactionList, EngineError> {
        let location = self
            .config
            .parse_location(location)
            .map_err(EngineError::Config)?;
        let apool = Apool::from_location(location)?;
        apool.get_create_snapshot_transactions()
    }

    pub fn get_sync_transactions(
        &self,
        source: &str,
        target: &str,
        options: &TransferOptions,
    ) -> Result<TransactionList, EngineError> {
        let source = self
            .config
            .parse_location(source)
            .map_err(EngineError::Config)?;
        let target = self
            .config
            .parse_location(target)
            .map_err(EngineError::Config)?;
        let source_apool = Apool::from_location(source)?;
        let target_apool = Apool::from_location(target)?;
        ApoolComparison::new(&source_apool, &target_apool).get_sync_transactions(options)
    }

    fn get_zpools(route: &Route) -> Result<Vec<Location>, EngineError> {
        let zpool_list = ZpoolListBuilder::new(route)
            .build()
            .map_err(EngineError::TransactionBuild)?
            .run()
            .map_err(EngineError::TransactionRun)?;
        zpool_list
            .assert_success()
            .map_err(EngineError::TransactionRun)?;
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
            locations.push(Location::new(
                route.to_owned(),
                Root::new(fragments[0].to_string()).map_err(EngineError::Config)?,
            ));
        }
        Ok(locations)
    }

    #[cfg(feature = "cli")]
    pub fn ls_cli(&self, json: bool, location: Option<&str>) -> Result<(), EngineError> {
        if let Some(location) = location {
            let (route, root) = Route::from_str_prefix(location).map_err(EngineError::Config)?;
            if root.is_empty() {
                if json {
                    self.print_json(&route)
                } else {
                    self.print_table(&route)
                }
            } else {
                let location = self
                    .config
                    .parse_location(location)
                    .map_err(EngineError::Config)?;
                Self::assert_command(location.get_route_ref(), "zfs".to_string())?;
                let apool = Apool::from_location(location)?;
                if json {
                    apool.print_json()
                } else {
                    apool.print_table()
                }
            }
        } else {
            let route = Route::from_localhost(None);
            if json {
                self.print_json(&route)
            } else {
                self.print_table(&route)
            }
        }
    }

    pub fn print_json(&self, route: &Route) -> Result<(), EngineError> {
        if *route == Route::from_localhost(None) {
            for (alias, location) in self.config.get_apools_iter() {
                println!(
                    "{}",
                    json!({
                        "alias": alias.to_owned(),
                        "route": location.get_route_ref().to_string(),
                        "user": location.get_route_ref().get_user_ref(),
                        "root": location.get_root_ref().to_string(),
                    })
                );
            }
        }
        Self::assert_command(route, "zpool".to_string())?;
        for location in Self::get_zpools(route)? {
            if !self.config.contains(&location) {
                println!(
                    "{}",
                    json!({
                        "alias": None::<String>,
                        "route": location.get_route_ref().to_string(),
                        "user": location.get_route_ref().get_user_ref(),
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
        if *route == Route::from_localhost(None) {
            for (alias, location) in self.config.get_apools_iter() {
                table.push_row(vec![
                    alias.green().to_string(),
                    location.get_route_ref().to_string().green().to_string(),
                    location
                        .get_route_ref()
                        .get_user_ref()
                        .unwrap_or(" ")
                        .green()
                        .to_string(),
                    location.get_root_ref().to_string().green().to_string(),
                ]);
            }
        }
        Self::assert_command(route, "zpool".to_string())?;
        for location in Self::get_zpools(route)? {
            if !self.config.contains(&location) {
                table.push_row(vec![
                    " ".to_string(),
                    location.get_route_ref().to_string(),
                    location
                        .get_route_ref()
                        .get_user_ref()
                        .unwrap_or(" ")
                        .to_owned(),
                    location.get_root_ref().to_string(),
                ]);
            }
        }
        table.print();
        Ok(())
    }

    #[cfg(feature = "cli")]
    pub fn snap_cli(
        &self,
        outputfmt: &OutputFmt,
        confirmation: &Confirmation,
        force: bool,
        location: &str,
    ) -> Result<(), EngineError> {
        let force = Force::from_bool(force).map_err(EngineError::TransactionBuild)?;
        let loc = self
            .config
            .parse_location(location)
            .map_err(EngineError::Config)?;
        Self::assert_command(loc.get_route_ref(), "zfs".to_string())?;
        let transactions = self.get_snap_transactions(location)?;
        transactions
            .run_cli(outputfmt, confirmation, &force)
            .map_err(EngineError::TransactionCli)
    }

    #[cfg(feature = "cli")]
    pub fn sync_cli(
        &self,
        outputfmt: &OutputFmt,
        confirmation: &Confirmation,
        options: &TransferOptions,
        force: bool,
        source: &str,
        target: &str,
    ) -> Result<(), EngineError> {
        let force = Force::from_bool(force).map_err(EngineError::TransactionBuild)?;
        let source_loc = self
            .config
            .parse_location(source)
            .map_err(EngineError::Config)?;
        let target_loc = self
            .config
            .parse_location(target)
            .map_err(EngineError::Config)?;
        Self::assert_command(source_loc.get_route_ref(), "zfs".to_string())?;
        Self::assert_command(target_loc.get_route_ref(), "zfs".to_string())?;
        if options.rate_limit.is_some() {
            Self::assert_command(source_loc.get_route_ref(), "pv".to_string())?;
        }
        if options.compress.is_some() {
            Self::assert_command(source_loc.get_route_ref(), "xz".to_string())?;
            Self::assert_command(target_loc.get_route_ref(), "xz".to_string())?;
        }
        if options.insecure.is_some() {
            Self::assert_command(source_loc.get_route_ref(), "nc".to_string())?;
            Self::assert_command(target_loc.get_route_ref(), "nc".to_string())?;
        }
        let transactions = self.get_sync_transactions(source, target, options)?;
        transactions
            .run_cli(outputfmt, confirmation, &force)
            .map_err(EngineError::TransactionCli)
    }
}
