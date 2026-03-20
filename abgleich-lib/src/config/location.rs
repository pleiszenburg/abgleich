use std::str::FromStr;
use std::string::ToString;

use tracing::debug;

use crate::consts::{LOCALHOST, USER_DELIMITER};

use super::errors::ConfigError;
use super::root::Root;
use super::route::Route;

pub struct Location {
    route: Route,
    user: Option<String>,
    root: Root,
}

impl Location {
    #[must_use]
    pub const fn get_root_ref(&self) -> &Root {
        &self.root
    }

    #[must_use]
    pub const fn get_route_ref(&self) -> &Route {
        &self.route
    }

    #[must_use]
    pub fn get_user_ref(&self) -> Option<&str> {
        self.user.as_deref()
    }

    #[must_use]
    pub fn with_route(&self, route: Route) -> Self {
        Self {
            route,
            user: self.user.clone(),
            root: self.root.clone(),
        }
    }

    fn parse_user(user: Option<&str>) -> Result<Option<String>, ConfigError> {
        match user {
            Some(user) => {
                if user.is_empty() {
                    return Err(ConfigError::LocationUserEmptyError);
                }
                Ok(Some(user.to_owned()))
            }
            _ => Ok(None),
        }
    }
}

#[allow(clippy::to_string_trait_impl)]
impl ToString for Location {
    fn to_string(&self) -> String {
        self.user.as_ref().map_or_else(
            || format!("{}:{}", self.route.to_string(), self.root.as_str()),
            |user| {
                format!(
                    "{}:{user}{USER_DELIMITER}{}",
                    self.route.to_string(),
                    self.root.as_str()
                )
            },
        )
    }
}

impl FromStr for Location {
    type Err = ConfigError;

    fn from_str(raw: &str) -> Result<Self, ConfigError> {
        debug!("parsing raw location '{}'", raw);
        let fragments: Vec<&str> = raw.split(':').collect();
        let (route, root) = match fragments.len() {
            1 => (LOCALHOST, fragments[0]),
            2 => (fragments[0], fragments[1]),
            _ => return Err(ConfigError::LocationFragmentsError),
        };
        let fragments: Vec<&str> = root.split(USER_DELIMITER).collect();
        let (user, root) = match fragments.len() {
            1 => (None, fragments[0]),
            2 => (Some(fragments[0]), fragments[1]),
            _ => return Err(ConfigError::LocationFragmentsError),
        };
        Ok(Self {
            route: Route::from_str(route)?,
            user: Self::parse_user(user)?,
            root: Root::from_str(root)?,
        })
    }
}

impl Clone for Location {
    fn clone(&self) -> Self {
        Self {
            root: self.root.clone(),
            route: self.route.clone(),
            user: self.user.clone(),
        }
    }
}

impl PartialEq for Location {
    fn eq(&self, other: &Self) -> bool {
        if self.get_root_ref() != other.get_root_ref() {
            return false;
        }
        if self.get_route_ref() != other.get_route_ref() {
            return false;
        }
        if self.get_user_ref() != other.get_user_ref() {
            return false;
        }
        true
    }
}
