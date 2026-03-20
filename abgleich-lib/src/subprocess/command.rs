use std::slice::Iter;
use std::string::ToString;

use shlex::try_join;

use crate::config::{Location, Route};

use super::errors::SubprocessError;
use super::proc::Proc;

pub struct Command {
    program: String,
    arguments: Vec<String>,
}

impl Command {
    pub fn new(program: String, arguments: Vec<String>) -> Result<Self, SubprocessError> {
        for argument in &arguments {
            if argument.contains('\0') {
                return Err(SubprocessError::ProcNullByteError);
            }
        }
        Ok(Self { program, arguments })
    }

    #[must_use]
    pub fn get_program_ref(&self) -> &str {
        &self.program
    }

    pub fn iter_arguments(&self) -> Iter<'_, String> {
        self.arguments.iter()
    }

    pub fn run(&self) -> Result<Proc, SubprocessError> {
        Proc::from_command(self, None)
    }

    pub fn with_sudo(&self) -> Result<Self, SubprocessError> {
        let mut arguments = self.arguments.clone();
        arguments.insert(0, self.program.clone());
        Self::new("sudo".to_owned(), arguments)
    }

    pub fn with_user(&self, name: &str) -> Result<Self, SubprocessError> {
        if name == "root" {
            return self.with_sudo();
        }
        let mut arguments = self.arguments.clone();
        arguments.insert(0, self.program.clone());
        arguments.insert(0, name.to_owned());
        arguments.insert(0, "-u".to_string());
        Self::new("sudo".to_owned(), arguments)
    }

    pub fn on_host(&self, host: &str) -> Result<Self, SubprocessError> {
        if host == "localhost" {
            return Ok(self.clone());
        }
        Self::new("ssh".to_string(), vec![host.to_string(), self.to_string()])
    }

    pub fn on_hosts(&self, route: &[&str]) -> Result<Self, SubprocessError> {
        match route.len() {
            0 => Ok(self.clone()),
            1 => self.on_host(route[0]),
            #[allow(clippy::missing_panics_doc)]
            _ => self
                .on_host(route.last().expect("infallible"))?
                .on_hosts(&route[..route.len() - 1]),
        }
    }

    pub fn on_location(&self, location: &Location) -> Result<Self, SubprocessError> {
        let command = match location.get_user_ref() {
            Some(user) => self.with_user(user)?,
            _ => self.clone(),
        };
        command.on_route(location.get_route_ref())
    }

    pub fn on_route(&self, route: &Route) -> Result<Self, SubprocessError> {
        let hosts: Vec<&str> = route
            .get_hosts_iter()
            .map(std::string::String::as_str)
            .collect();
        self.on_hosts(&hosts)
    }
}

#[allow(clippy::to_string_trait_impl)]
impl ToString for Command {
    fn to_string(&self) -> String {
        let mut fragments: Vec<String> = Vec::new();
        for argument in &self.arguments {
            fragments.push(argument.clone());
        }
        let mut fragment_refs: Vec<&str> =
            fragments.iter().map(std::string::String::as_str).collect();
        fragment_refs.insert(0, &self.program);
        try_join(fragment_refs).expect("infallible: null bytes excluded earlier")
    }
}

impl Clone for Command {
    fn clone(&self) -> Self {
        Self {
            program: self.program.clone(),
            arguments: self.arguments.clone(),
        }
    }
}
