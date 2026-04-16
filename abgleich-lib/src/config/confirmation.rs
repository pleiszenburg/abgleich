pub enum Confirmation {
    Yes,
    Manual,
}

impl Confirmation {
    #[must_use]
    pub const fn from_yes_flag(flag: bool) -> Self {
        if flag {
            Self::Yes
        } else {
            Self::Manual
        }
    }
}
