use serde_json::json;
use tracing::info;

use crate::subprocess::{Command, OutcomeSuccess};

use super::errors::TransactionRunError;
use super::meta::TransactionMeta;
use super::outcome::TransactionOutcome;

pub struct TransactionJsonFields {
    pub description: String,
    pub command: String,
}

pub struct TransactionTableRow {
    pub description: String,
    pub command: String,
}

pub struct Transaction {
    meta: TransactionMeta,
    command: Command,
    mutation: bool,
}

impl Transaction {
    #[must_use]
    pub const fn new(
        meta: TransactionMeta,
        command: Command,
        mutation: bool,
    ) -> Self {
        Self {
            meta,
            command,
            mutation,
        }
    }

    pub fn run(&self) -> Result<TransactionOutcome, TransactionRunError> {
        if self.mutation {
            println!("{}",
                json!({
                    "message": format!("[RUN] {}", self.meta.to_description(false, false)),
                    "command": self.command.to_string(),
                })
            );
        } else {
            info!(
                message = format!("[RUN] {}", self.meta.to_description(false, false)),
                command = self.command.to_string(),
            );
        }
        let outcome = self
            .command
            .run()
            .map_err(TransactionRunError::Subprocess)?
            .communicate()
            .map_err(TransactionRunError::Subprocess)?;
        let success = outcome.success();
        match &success {
            OutcomeSuccess::Yes => {
                if self.mutation {
                    println!("{}", json!({"message": format!("[OK] {}", self.meta.to_description(false, false))}));
                } else {
                    info!(message = format!("[OK] {}", self.meta.to_description(false, false)));
                }
            },
            OutcomeSuccess::No(reason) => {
                if self.mutation {
                    println!("{}", json!({"message": format!("[FAILED: {reason}] {}", self.meta.to_description(false, false))}));
                } else {
                    info!(message = format!("[FAILED: {reason}] {}", self.meta.to_description(false, false)));
                }
            }
        }
        let data = outcome
            .stdout_as_str_ref()
            .map_err(TransactionRunError::Subprocess)?
            .to_string();
        let data = match &self.meta {
            TransactionMeta::Inventory(meta) => meta.handle_root_output(data),
            _ => data,
        };
        Ok(TransactionOutcome::new(
            success,
            Some(data),
            self.meta.clone(),
        ))
    }

    #[must_use]
    pub fn to_json_row(&self) -> TransactionJsonFields {
        TransactionJsonFields {
            description: self.meta.to_description(false, false),
            command: self.command.to_string(),
        }
    }

    #[must_use]
    pub fn to_table_row(&self) -> TransactionTableRow {
        TransactionTableRow {
            description: self.meta.to_description(true, true),
            command: self.command.to_string(),
        }
    }
}
