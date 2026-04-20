use std::slice::Iter;
use std::str::FromStr;
use std::string::ToString;

use tracing::debug;

use crate::consts::{HOSTS_DELIMITER, HOSTS_SUFFIX, LOCALHOST, USER_SUFFIX};

use super::errors::ConfigError;

#[derive(Clone, PartialEq, Eq, Hash)]
pub struct Route {
    hosts: Vec<String>,
    user: Option<String>,
}

impl Route {
    #[must_use]
    pub const fn from_localhost(user: Option<String>) -> Self {
        Self {
            hosts: Vec::new(),
            user,
        }
    }

    pub fn from_str_prefix(raw: &'_ str) -> Result<(Self, &'_ str), ConfigError> {
        debug!("parsing raw route '{}'", raw);
        if raw.is_empty() {
            return Ok((Self::from_localhost(None), raw));
        }
        let (hosts, raw) = if raw.contains(HOSTS_SUFFIX) {
            let fragments: Vec<&str> = raw.split(HOSTS_SUFFIX).collect();
            if fragments.len() > 2 {
                return Err(ConfigError::RouteParser {
                    msg: format!("encountered hosts suffix '{HOSTS_SUFFIX}' more than once"),
                });
            }
            let mut hosts: Vec<&str> = fragments[0].split(HOSTS_DELIMITER).collect();
            if !hosts.is_empty() && (hosts[0] == LOCALHOST || hosts[0].is_empty()) {
                hosts.remove(0);
            }
            if hosts.iter().filter(|host| **host == LOCALHOST).count() > 0 {
                return Err(ConfigError::RouteParser {
                    msg: "encountered host 'localhost' in unexpected position".to_string(),
                });
            }
            let hosts: Vec<String> = hosts.iter().map(std::string::ToString::to_string).collect();
            (hosts, fragments[1])
        } else {
            (Vec::<String>::new(), raw)
        };
        let (user, raw) = if raw.contains(USER_SUFFIX) {
            let fragments: Vec<&str> = raw.split(USER_SUFFIX).collect();
            if fragments.len() > 2 {
                return Err(ConfigError::RouteParser {
                    msg: format!("encountered user suffix '{USER_SUFFIX}' more than once"),
                });
            }
            let user = fragments[0].to_string();
            if user.is_empty() {
                return Err(ConfigError::RouteParser {
                    msg: "user field provided but empty".to_string(),
                });
            }
            (Some(user), fragments[1])
        } else {
            (None, raw)
        };
        Ok((Self { hosts, user }, raw))
    }

    #[must_use]
    pub fn get_host_ref(&self) -> &str {
        self.hosts.last().map_or(LOCALHOST, |host| host.as_str())
    }

    pub fn get_hosts_iter(&self) -> Iter<'_, String> {
        self.hosts.iter()
    }

    #[must_use]
    pub fn get_user_ref(&self) -> Option<&str> {
        self.user.as_deref()
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
        let (route, raw) = Self::from_str_prefix(raw)?;
        if !raw.is_empty() {
            return Err(ConfigError::RouteParser {
                msg: "unexpected route fragment".to_string(),
            });
        }
        Ok(route)
    }
}

#[allow(clippy::to_string_trait_impl)]
impl ToString for Route {
    fn to_string(&self) -> String {
        let hosts = if self.hosts.is_empty() {
            LOCALHOST.to_string()
        } else {
            self.hosts.join(&HOSTS_DELIMITER.to_string())
        };
        self.user.as_ref().map_or_else(
            || format!("{hosts}{HOSTS_SUFFIX}"),
            |user| format!("{hosts}{HOSTS_SUFFIX}{user}{USER_SUFFIX}"),
        )
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
                user: None,
            },
            Self {
                hosts: source.hosts[common_len..].to_vec(),
                user: source.user.clone(),
            },
            Self {
                hosts: target.hosts[common_len..].to_vec(),
                user: target.user.clone(),
            },
        )
    }
}
