use clap::Parser;
use tracing::debug;

use crate::config::{Confirmation, OutputFmt, TransferOptions};
use crate::consts::VERSION;
use crate::engine::Engine;

use super::command::{Cli, Commands};
use super::errors::CliError;
use super::tracing::tracing_init;

pub fn dispatch() -> Result<(), CliError> {
    tracing_init()?;
    debug!(version = VERSION);

    let args = Cli::parse();
    match args.command {
        Commands::Free {
            json,
            yes,
            force,
            source,
            target,
        } => {
            Engine::from_detect()
                .map_err(CliError::Engine)?
                .free_cli(&OutputFmt::from_json_flag(json), &Confirmation::from_yes_flag(yes), force, &source, &target)
                .map_err(CliError::Engine)?;
        }

        Commands::Ls { json, location } => {
            Engine::from_detect()
                .map_err(CliError::Engine)?
                .ls_cli(json, location.as_deref())
                .map_err(CliError::Engine)?;
        }

        Commands::Snap {
            json,
            yes,
            force,
            location,
        } => {
            Engine::from_detect()
                .map_err(CliError::Engine)?
                .snap_cli(&OutputFmt::from_json_flag(json), &Confirmation::from_yes_flag(yes), force, &location)
                .map_err(CliError::Engine)?;
        }

        Commands::Sync {
            json,
            yes,
            direct,
            force,
            rate_limit,
            compress,
            insecure,
            source,
            target,
        } => {
            let options = TransferOptions::new()
                .with_compress(compress)
                .with_rate_limit(rate_limit)
                .with_insecure(insecure).map_err(CliError::Config)?
                .with_direct(direct).map_err(CliError::Config)?;
            Engine::from_detect()
                .map_err(CliError::Engine)?
                .sync_cli(&OutputFmt::from_json_flag(json), &Confirmation::from_yes_flag(yes), &options, force, &source, &target)
                .map_err(CliError::Engine)?;
        }

        Commands::Version {} => {
            println!("{VERSION}");
        }
    }
    Ok(())
}
