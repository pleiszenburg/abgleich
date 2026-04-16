use super::error::PropertyError;

pub struct RawProperty {
    pub dataset: String,
    pub name: String,
    pub value: String,
    pub origin: String,
}

impl RawProperty {
    pub fn from_line(line: &str) -> Result<Self, PropertyError> {
        let mut fragments = line.split('\t');
        let raw_property = Self {
            dataset: fragments
                .next()
                .ok_or_else(|| PropertyError::ParseFragments{line: line.to_string()})?
                .to_string(),
            name: fragments
                .next()
                .ok_or_else(|| PropertyError::ParseFragments{line: line.to_string()})?
                .to_string(),
            value: fragments
                .next()
                .ok_or_else(|| PropertyError::ParseFragments{line: line.to_string()})?
                .to_string(),
            origin: fragments
                .next()
                .ok_or_else(|| PropertyError::ParseFragments{line: line.to_string()})?
                .to_string(),
        };
        Ok(raw_property)
    }

    pub fn from_raws(raw: &str) -> Result<Vec<Self>, PropertyError> {
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
