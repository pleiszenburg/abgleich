pub enum OutputFmt {
    Json,
    Human,
}

impl OutputFmt {
    #[must_use]
    pub const fn from_json_flag(flag: bool) -> Self {
        if flag {
            Self::Json
        } else {
            Self::Human
        }
    }
}
