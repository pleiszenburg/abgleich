use std::env::{current_dir, home_dir};
use std::fs::OpenOptions;
use std::io::Read;
use std::path::{Path, PathBuf};
use std::str::FromStr;

use indexmap::IndexMap;
use indexmap::map::Iter as IMIter;
use serde::{Deserialize, Serialize};
use serde_yaml_ng as serde_yaml;
use tracing::{debug, info};

use crate::consts::{NAME, VAR_CONFIG};
use crate::sys::envvar2string;
use crate::traits::{FromSerializable, ToSerializable};

use super::errors::ConfigError;
use super::location::Location;

#[derive(Deserialize, Serialize)]
#[allow(unused)]
pub struct ConfigSerializable {
    pub apools: IndexMap<String, String>,
}

#[allow(unused)]
pub struct Config {
    apools: IndexMap<String, Location>,
}

impl Config {
    #[allow(clippy::new_without_default)]
    #[must_use]
    pub fn new() -> Self {
        Self {
            apools: IndexMap::new(),
        }
    }

    pub fn from_detect() -> Result<Self, ConfigError> {
        match Self::detect() {
            Ok(path) => Self::from_path(&path),
            Err(ConfigError::ConfigNotFoundError) => {
                info!("no configuration found, starting empty");
                Ok(Self::new())
            }
            Err(err) => Err(err),
        }
    }

    pub fn from_path(path: &Path) -> Result<Self, ConfigError> {
        let mut f = OpenOptions::new()
            .read(true)
            .open(path)
            .map_err(ConfigError::IoError)?;
        let mut buf = Vec::new();
        f.read_to_end(&mut buf).map_err(ConfigError::IoError)?;
        drop(f);
        let raw = String::from_utf8(buf).map_err(ConfigError::Utf8DecodingError)?;
        let config: ConfigSerializable =
            serde_yaml::from_str(&raw).map_err(ConfigError::YamlDeserializingError)?;
        Self::from_serializable(config)
    }

    #[must_use]
    pub fn contains(&self, location: &Location) -> bool {
        for known_location in self.apools.values() {
            if known_location == location {
                return true;
            }
        }
        false
    }

    fn detect() -> Result<PathBuf, ConfigError> {
        if let Some(path) = Self::detect_env() {
            return Ok(path);
        }
        if let Some(path) = Self::detect_cwd() {
            return Ok(path);
        }
        if let Some(path) = Self::detect_home() {
            return Ok(path);
        }
        if let Some(path) = Self::detect_etc() {
            return Ok(path);
        }
        Err(ConfigError::ConfigNotFoundError)
    }

    fn detect_env() -> Option<PathBuf> {
        envvar2string(VAR_CONFIG).and_then(|path| {
            debug!("detected configuration location passed through environment variable");
            PathBuf::from_str(&path).ok()
        })
    }

    fn detect_cwd() -> Option<PathBuf> {
        current_dir().map_or(None, |mut path| {
            path.push(format!("{NAME}.yaml"));
            if path.is_file() {
                debug!("detected configuration file in current working directory");
                Some(path)
            } else {
                None
            }
        })
    }

    fn detect_etc() -> Option<PathBuf> {
        PathBuf::from_str(&format!("/etc/{NAME}.yaml")).map_or(None, |path| {
            if path.is_file() {
                debug!("detected configuration file in /etc");
                Some(path)
            } else {
                None
            }
        })
    }

    fn detect_home() -> Option<PathBuf> {
        home_dir().and_then(|mut path| {
            path.push(format!(".{NAME}.yaml"));
            if path.is_file() {
                debug!("detected configuration file in home directory of current user");
                Some(path)
            } else {
                None
            }
        })
    }

    #[must_use]
    pub fn get_apools_iter(&self) -> IMIter<'_, String, Location> {
        self.apools.iter()
    }

    #[must_use]
    pub fn get_location_ref(&self, alias: &str) -> Option<&Location> {
        self.apools.get(alias)
    }

    pub fn parse_location(&self, location: &str) -> Result<Location, ConfigError> {
        self.get_location_ref(location).map_or_else(
            || Location::from_str(location),
            |location| Ok(location.clone()),
        )
    }
}

impl FromSerializable<ConfigSerializable, ConfigError> for Config {
    fn from_serializable(serializable: ConfigSerializable) -> Result<Self, ConfigError> {
        let mut apools = IndexMap::new();
        for (alias, apool) in serializable.apools {
            apools.insert(alias, Location::from_str(&apool)?);
        }
        Ok(Self { apools })
    }
}

impl ToSerializable<ConfigSerializable, ConfigError> for Config {
    fn to_serializable(&self) -> Result<ConfigSerializable, ConfigError> {
        let mut apools = IndexMap::new();
        for (alias, apool) in &self.apools {
            apools.insert(alias.to_owned(), apool.to_string());
        }
        Ok(ConfigSerializable { apools })
    }
}
