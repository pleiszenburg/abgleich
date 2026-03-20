use super::super::errors::EngineError;

pub struct RawProperty {
    pub dataset: String,
    pub name: String,
    pub value: String,
    pub meta: String,
}

impl RawProperty {
    pub fn from_line(line: &str) -> Result<Self, EngineError> {
        let mut fragments = line.split('\t');
        let raw_property = Self {
            dataset: fragments
                .next()
                .ok_or(EngineError::PropertyParseFragmentsError)?
                .to_string(),
            name: fragments
                .next()
                .ok_or(EngineError::PropertyParseFragmentsError)?
                .to_string(),
            value: fragments
                .next()
                .ok_or(EngineError::PropertyParseFragmentsError)?
                .to_string(),
            meta: fragments
                .next()
                .ok_or(EngineError::PropertyParseFragmentsError)?
                .to_string(),
        };
        Ok(raw_property)
    }

    pub fn from_raws(raw: &str) -> Result<Vec<Self>, EngineError> {
        let lines = raw.split('\n');
        let chars: &[_] = &[' ', '\t'];
        let mut raw_properties: Vec<Self> = Vec::new();
        for line in lines {
            let line_cleaned = line.trim_matches(chars);
            if line_cleaned.is_empty() {
                continue;
            }
            let raw_property = Self::from_line(line_cleaned)?;
            raw_properties.push(raw_property);
        }
        Ok(raw_properties)
    }
}
