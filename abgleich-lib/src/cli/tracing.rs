use std::io::stderr;

use tracing_subscriber::filter::LevelFilter;
use tracing_subscriber::fmt::layer;
use tracing_subscriber::layer::SubscriberExt;
use tracing_subscriber::util::SubscriberInitExt;
use tracing_subscriber::{Layer, registry};

use crate::sys::get_loglevel;

use super::errors::CliError;

pub fn tracing_init() -> Result<(), CliError> {
    let mut layers = Vec::new();
    {
        let level = get_loglevel().map_err(CliError::SysError)?;
        let filter = LevelFilter::from_level(level); // implicit "max level"
        let layer = layer()
            .json()
            .with_writer(stderr)
            .with_current_span(false)
            .with_filter(filter)
            .boxed();
        layers.push(layer);
    }
    registry().with(layers).init();
    Ok(())
}
