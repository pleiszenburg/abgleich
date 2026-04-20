use std::str::FromStr;
use std::string::ToString;

use tracing::debug;

use super::errors::ConfigError;
use super::root::Root;
use super::route::Route;

#[derive(Clone, PartialEq, Eq)]
pub struct Location {
    route: Route,
    root: Root,
}

impl Location {
    #[must_use]
    pub const fn new(route: Route, root: Root) -> Self {
        Self { route, root }
    }

    #[must_use]
    pub const fn get_root_ref(&self) -> &Root {
        &self.root
    }

    #[must_use]
    pub const fn get_route_ref(&self) -> &Route {
        &self.route
    }

    #[must_use]
    pub fn with_route(&self, route: Route) -> Self {
        Self {
            route,
            root: self.root.clone(),
        }
    }
}

#[allow(clippy::to_string_trait_impl)]
impl ToString for Location {
    fn to_string(&self) -> String {
        format!("{}{}", self.route.to_string(), self.root.as_str())
    }
}

impl FromStr for Location {
    type Err = ConfigError;

    fn from_str(raw: &str) -> Result<Self, ConfigError> {
        debug!("parsing raw location '{}'", raw);
        let (route, raw) = Route::from_str_prefix(raw)?;
        Ok(Self {
            route,
            root: Root::from_str(raw)?,
        })
    }
}
