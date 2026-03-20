use std::slice::Iter;
use std::str::FromStr;
use std::string::ToString;

use crate::consts::LOCALHOST;

use super::errors::ConfigError;

pub struct Route {
    hosts: Vec<String>,
}

impl Route {
    #[must_use]
    pub const fn from_localhost() -> Self {
        Self { hosts: Vec::new() }
    }

    #[must_use]
    pub fn get_host_ref(&self) -> &str {
        self.hosts.last().map_or(LOCALHOST, |host| host.as_str())
    }

    pub fn get_hosts_iter(&self) -> Iter<'_, String> {
        self.hosts.iter()
    }

    #[must_use]
    pub const fn len(&self) -> usize {
        self.hosts.len()
    }

    #[must_use]
    pub const fn is_empty(&self) -> bool {
        self.hosts.is_empty()
    }
}

impl FromStr for Route {
    type Err = ConfigError;

    fn from_str(raw: &str) -> Result<Self, ConfigError> {
        let mut hosts: Vec<&str> = raw.split('/').collect();
        if !hosts.is_empty() && (hosts[0] == LOCALHOST || hosts[0].is_empty()) {
            hosts.remove(0);
        }
        if hosts.iter().filter(|host| **host == LOCALHOST).count() > 0 {
            return Err(ConfigError::LocationLocalhostPositionError);
        }
        Ok(Self {
            hosts: hosts.iter().map(std::string::ToString::to_string).collect(),
        })
    }
}

#[allow(clippy::to_string_trait_impl)]
impl ToString for Route {
    fn to_string(&self) -> String {
        if self.hosts.is_empty() {
            return LOCALHOST.to_string();
        }
        self.hosts.join("/")
    }
}

impl Clone for Route {
    fn clone(&self) -> Self {
        Self {
            hosts: self.hosts.clone(),
        }
    }
}

impl PartialEq for Route {
    fn eq(&self, other: &Self) -> bool {
        if self.len() != other.len() {
            return false;
        }
        for (a, b) in self.get_hosts_iter().zip(other.get_hosts_iter()) {
            if a != b {
                return false;
            }
        }
        true
    }
}

impl Route {
    /// Returns true if any host appears twice in direct succession, e.g. `a/b/b/c`.
    ///
    /// Such routes are rejected by `--direct` because after route rewriting the
    /// remainder can start with the same host as the last entry-route hop,
    /// causing the pipe to SSH from a host back to itself.
    #[must_use]
    pub fn has_consecutive_duplicates(&self) -> bool {
        self.hosts.windows(2).any(|w| w[0] == w[1])
    }

    #[must_use]
    pub fn split_common_prefix(source: &Self, target: &Self) -> (Self, Self, Self) {
        let common_len = source
            .hosts
            .iter()
            .zip(target.hosts.iter())
            .take_while(|(a, b)| a == b)
            .count();
        (
            Self {
                hosts: source.hosts[..common_len].to_vec(),
            },
            Self {
                hosts: source.hosts[common_len..].to_vec(),
            },
            Self {
                hosts: target.hosts[common_len..].to_vec(),
            },
        )
    }
}
