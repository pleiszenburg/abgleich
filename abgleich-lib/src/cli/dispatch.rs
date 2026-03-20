use clap::Parser;
use tracing::debug;

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
                .map_err(CliError::EngineError)?
                .free_cli(json, yes, force, &source, &target)
                .map_err(CliError::EngineError)?;
        }

        Commands::Ls { json, location } => {
            Engine::from_detect()
                .map_err(CliError::EngineError)?
                .ls_cli(json, location.as_deref())
                .map_err(CliError::EngineError)?;
        }

        Commands::Snap {
            json,
            yes,
            force,
            location,
        } => {
            Engine::from_detect()
                .map_err(CliError::EngineError)?
                .snap_cli(json, yes, force, &location)
                .map_err(CliError::EngineError)?;
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
            Engine::from_detect()
                .map_err(CliError::EngineError)?
                .sync_cli(json, yes, direct, force, rate_limit, compress, insecure, &source, &target)
                .map_err(CliError::EngineError)?;
        }

        Commands::Version {} => {
            println!("{VERSION}");
        }
    }
    Ok(())
}
