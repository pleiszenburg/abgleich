use crate::subprocess::OutcomeSuccess;
use crate::transaction::TransactionRunError;

use super::meta::TransactionMeta;

pub struct TransactionOutcome {
    success: OutcomeSuccess,
    data: Option<String>,
    meta: TransactionMeta,
}

impl TransactionOutcome {
    pub const fn new(success: OutcomeSuccess, data: Option<String>, meta: TransactionMeta) -> Self {
        Self {
            success,
            data,
            meta,
        }
    }

    pub fn assert_success(&self) -> Result<(), TransactionRunError> {
        match &self.success {
            OutcomeSuccess::Yes => Ok(()),
            OutcomeSuccess::No(reason) => Err(TransactionRunError::Failed{
                reason: reason.clone(),
                description: self.meta.to_description(false, false)
            }),
        }
    }

    pub fn get_data_ref(&self) -> Option<&str> {
        self.data.as_deref()
    }

    pub const fn get_meta_ref(&self) -> &TransactionMeta {
        &self.meta
    }

    pub const fn is_successful(&self) -> bool {
        match &self.success {
            OutcomeSuccess::Yes => true,
            OutcomeSuccess::No(_) => false,
        }
    }
}
