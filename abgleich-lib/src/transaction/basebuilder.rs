use super::errors::TransactionBuildError;
use super::transaction::Transaction;

pub trait BaseBuilder {
    fn build(self) -> Result<Transaction, TransactionBuildError>;
}
