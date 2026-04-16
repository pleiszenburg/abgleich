#[cfg(feature = "cli")]
use inquire::Confirm;
use serde_json::json;
use tracing::error;

#[cfg(feature = "cli")]
use crate::config::{Confirmation, OutputFmt};
use crate::output::{Alignment, Table, TableColumn};
use crate::traits::Traverse;

#[cfg(feature = "cli")]
use super::errors::TransactionCliError;
use super::errors::TransactionRunError;
use super::force::Force;
use super::transaction::Transaction;

pub struct TransactionList {
    transactions: Vec<Transaction>,
}

impl Default for TransactionList {
    fn default() -> Self {
        Self::new()
    }
}

impl TransactionList {
    #[must_use]
    pub const fn new() -> Self {
        Self {
            transactions: Vec::new(),
        }
    }

    pub fn append(&mut self, transactions: &mut Self) {
        self.transactions.append(&mut transactions.transactions);
    }

    pub fn push(&mut self, transaction: Transaction) {
        self.transactions.push(transaction);
    }

    // "assert_success", based on non-zero exit-code or signal termination,
    // raises "transaction fail", optionally ignored with normal force.
    // In "transaction.run", before and after, lower-level sub-process errors
    // can occur, handled with full force if required.
    pub fn run(&self, force: &Force) -> Result<(), TransactionRunError> {
        let mut failures = 0usize;
        for transaction in &self.transactions {
            let outcome = match transaction.run() {
                Ok(outcome) => outcome,
                Err(err) => {
                    if *force == Force::Full {
                        error!(msg = "ignoring error with full force", traceback = err.traverse());
                        failures += 1;
                        continue;
                    }
                    return Err(err);
                }
            };
            match outcome.assert_success() {
                Ok(()) => {}
                Err(TransactionRunError::Failed{reason: _, description: _}) if *force != Force::No => failures += 1, // logged by transaction already
                Err(err) => return Err(err),
            }
        }
        if failures > 0 {
            return Err(TransactionRunError::SomeFailed(failures));
        }
        Ok(())
    }

    #[cfg(feature = "cli")]
    pub fn run_cli(&self, outputfmt: &OutputFmt, confirmation: &Confirmation, force: &Force) -> Result<(), TransactionCliError> {
        match outputfmt {
            OutputFmt::Human => self.print_table(),
            OutputFmt::Json => self.print_json(),
        }
        match confirmation {
            Confirmation::Manual => {
                let confirmation = Confirm::new("Run?")
                    .with_default(false)
                    .prompt()
                    .map_err(TransactionCliError::Inquire)?;
                if !confirmation {
                    return Ok(());
                }
            },
            Confirmation::Yes => println!("{}", json!({"run": true})),
        }
        self.run(force).map_err(TransactionCliError::Run)
    }

    pub fn print_json(&self) {
        for transaction in &self.transactions {
            let row = transaction.to_json_row();
            println!(
                "{}",
                json!({
                    "description": row.description,
                    "command": row.command,
                })
            );
        }
    }

    pub fn print_table(&self) {
        let mut table = Table::new(vec![
            TableColumn::new("description".to_string(), Alignment::Left),
            TableColumn::new("command".to_string(), Alignment::Left),
        ]);
        for transaction in &self.transactions {
            let row = transaction.to_table_row();
            table.push_row(vec![row.description, row.command]);
        }
        table.print();
    }
}
