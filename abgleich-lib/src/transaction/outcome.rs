use crate::transaction::TransactionError;

use super::meta::TransactionMeta;

pub struct TransactionOutcome {
    success: bool,
    data: Option<String>,
    meta: TransactionMeta,
}

impl TransactionOutcome {
    pub const fn new(success: bool, data: Option<String>, meta: TransactionMeta) -> Self {
        Self {
            success,
            data,
            meta,
        }
    }

    pub const fn assert_success(&self) -> Result<(), TransactionError> {
        if self.success {
            return Ok(());
        }
        Err(TransactionError::FailedError)
    }

    pub fn get_data_ref(&self) -> Option<&str> {
        self.data.as_deref()
    }

    pub const fn get_meta_ref(&self) -> &TransactionMeta {
        &self.meta
    }

    pub const fn is_successful(&self) -> bool {
        self.success
    }
}
