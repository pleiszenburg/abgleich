#[cfg(feature = "cli")]
use inquire::Confirm;
use serde_json::json;

use crate::output::{Alignment, Table, TableColumn};

use super::errors::TransactionError;
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

    pub fn run(&self, force: bool) -> Result<(), TransactionError> {
        let mut failures = 0usize;
        for transaction in &self.transactions {
            let result = transaction.run().and_then(|outcome| outcome.assert_success());
            match result {
                Ok(()) => {}
                Err(_) if force => failures += 1,
                Err(e) => return Err(e),
            }
        }
        if failures > 0 {
            return Err(TransactionError::SomeTransactionsFailed(failures));
        }
        Ok(())
    }

    #[cfg(feature = "cli")]
    pub fn run_cli(&self, json: bool, yes: bool, force: bool) -> Result<(), TransactionError> {
        if json {
            self.print_json()?;
        } else {
            self.print_table()?;
        }
        if !yes {
            let confirmation = Confirm::new("Run?")
                .with_default(false)
                .prompt()
                .map_err(TransactionError::InquireError)?;
            if !confirmation {
                return Ok(());
            }
        }
        self.run(force)
    }

    pub fn print_json(&self) -> Result<(), TransactionError> {
        for transaction in &self.transactions {
            let row = transaction.to_json_row()?;
            println!(
                "{}",
                json!({
                    "description": row.description,
                    "command": row.chain,
                })
            );
        }
        Ok(())
    }

    pub fn print_table(&self) -> Result<(), TransactionError> {
        let mut table = Table::new(vec![
            TableColumn::new("description".to_string(), Alignment::Left),
            TableColumn::new("command".to_string(), Alignment::Left),
        ]);
        for transaction in &self.transactions {
            let row = transaction.to_table_row()?;
            table.push_row(vec![row.description, row.chain]);
        }
        table.print();
        Ok(())
    }
}
