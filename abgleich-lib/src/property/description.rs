use indexmap::IndexMap;
use tracing::trace;

use super::bool::BoolValue;
use super::error::PropertyError;
use super::float::FloatValue;
use super::int::IntValue;
use super::optionaluint::OptionalUIntValue;
use super::property::{BaseProperty, ImmutableProperty, MutableProperty};
use super::raw::RawProperty;
use super::snap::SnapValue;
use super::string::StringValue;
use super::type_::TypeValue;
use super::uint::UIntValue;

pub struct Description {
    pub abgleich_diff: Option<MutableProperty<BoolValue>>,
    pub abgleich_format: Option<MutableProperty<StringValue>>,
    pub abgleich_overlap: Option<MutableProperty<IntValue>>,
    pub abgleich_snap: Option<MutableProperty<SnapValue>>,
    pub abgleich_sync: Option<MutableProperty<BoolValue>>,
    pub abgleich_threshold: Option<MutableProperty<UIntValue>>,
    pub atime: Option<MutableProperty<BoolValue>>,
    pub available: Option<ImmutableProperty<IntValue>>,
    pub canmount: Option<MutableProperty<BoolValue>>,
    pub checksum: Option<MutableProperty<BoolValue>>,
    pub compression: Option<MutableProperty<StringValue>>,
    pub compressratio: Option<ImmutableProperty<FloatValue>>,
    pub creation: Option<ImmutableProperty<IntValue>>,
    pub dedup: Option<MutableProperty<BoolValue>>,
    pub encryption: Option<MutableProperty<BoolValue>>,
    pub filesystem_count: Option<MutableProperty<OptionalUIntValue>>,
    pub filesystem_limit: Option<MutableProperty<OptionalUIntValue>>,
    pub guid: Option<ImmutableProperty<UIntValue>>,
    pub logicalreferenced: Option<ImmutableProperty<UIntValue>>,
    pub logicalused: Option<ImmutableProperty<UIntValue>>,
    pub mounted: Option<ImmutableProperty<BoolValue>>,
    pub mountpoint: Option<MutableProperty<StringValue>>,
    pub name: String,
    pub readonly: Option<MutableProperty<BoolValue>>,
    pub redundant_metadata: Option<MutableProperty<StringValue>>,
    pub refcompressratio: Option<ImmutableProperty<FloatValue>>,
    pub referenced: Option<ImmutableProperty<UIntValue>>,
    pub refquota: Option<MutableProperty<UIntValue>>,
    pub relatime: Option<MutableProperty<BoolValue>>,
    pub quota: Option<MutableProperty<UIntValue>>,
    pub sharenfs: Option<MutableProperty<BoolValue>>,
    pub snapshot_count: Option<MutableProperty<OptionalUIntValue>>,
    pub snapshot_limit: Option<MutableProperty<OptionalUIntValue>>,
    pub sync: Option<MutableProperty<StringValue>>,
    pub type_: Option<ImmutableProperty<TypeValue>>,
    pub used: Option<ImmutableProperty<UIntValue>>,
    pub usedbychildren: Option<ImmutableProperty<UIntValue>>,
    pub usedbydataset: Option<ImmutableProperty<UIntValue>>,
    pub usedbyrefreservation: Option<ImmutableProperty<UIntValue>>,
    pub usedbysnapshots: Option<ImmutableProperty<UIntValue>>,
    pub version: Option<ImmutableProperty<UIntValue>>,
    pub volmode: Option<MutableProperty<StringValue>>,
    pub written: Option<ImmutableProperty<UIntValue>>,
}

impl Description {
    #[must_use]
    const fn new(name: String) -> Self {
        Self {
            abgleich_diff: None,
            abgleich_format: None,
            abgleich_overlap: None,
            abgleich_snap: None,
            abgleich_sync: None,
            abgleich_threshold: None,
            atime: None,
            available: None,
            canmount: None,
            checksum: None,
            compression: None,
            compressratio: None,
            creation: None,
            dedup: None,
            encryption: None,
            filesystem_count: None,
            filesystem_limit: None,
            guid: None,
            logicalreferenced: None,
            logicalused: None,
            mounted: None,
            mountpoint: None,
            name,
            readonly: None,
            redundant_metadata: None,
            refcompressratio: None,
            referenced: None,
            refquota: None,
            relatime: None,
            quota: None,
            sharenfs: None,
            snapshot_count: None,
            snapshot_limit: None,
            sync: None,
            type_: None,
            used: None,
            usedbychildren: None,
            usedbydataset: None,
            usedbyrefreservation: None,
            usedbysnapshots: None,
            version: None,
            volmode: None,
            written: None,
        }
    }

    fn fill(&mut self, raw: &RawProperty) -> Result<(), PropertyError> {
        match raw.name.as_str() {
            "abgleich:diff" => self.abgleich_diff = Some(MutableProperty::from_raw(raw)?),
            "abgleich:format" => self.abgleich_format = Some(MutableProperty::from_raw(raw)?),
            "abgleich:overlap" => self.abgleich_overlap = Some(MutableProperty::from_raw(raw)?),
            "abgleich:snap" => self.abgleich_snap = Some(MutableProperty::from_raw(raw)?),
            "abgleich:sync" => self.abgleich_sync = Some(MutableProperty::from_raw(raw)?),
            "abgleich:threshold" => self.abgleich_threshold = Some(MutableProperty::from_raw(raw)?),
            "atime" => self.atime = Some(MutableProperty::from_raw(raw)?),
            "available" => self.available = Some(ImmutableProperty::from_raw(raw)?),
            "canmount" => self.canmount = Some(MutableProperty::from_raw(raw)?),
            "checksum" => self.checksum = Some(MutableProperty::from_raw(raw)?),
            "compression" => self.compression = Some(MutableProperty::from_raw(raw)?),
            "compressratio" => self.compressratio = Some(ImmutableProperty::from_raw(raw)?),
            "creation" => self.creation = Some(ImmutableProperty::from_raw(raw)?),
            "dedup" => self.dedup = Some(MutableProperty::from_raw(raw)?),
            "encryption" => self.encryption = Some(MutableProperty::from_raw(raw)?),
            "filesystem_count" => self.filesystem_count = Some(MutableProperty::from_raw(raw)?),
            "filesystem_limit" => self.filesystem_limit = Some(MutableProperty::from_raw(raw)?),
            "guid" => self.guid = Some(ImmutableProperty::from_raw(raw)?),
            "logicalreferenced" => self.logicalreferenced = Some(ImmutableProperty::from_raw(raw)?),
            "logicalused" => self.logicalused = Some(ImmutableProperty::from_raw(raw)?),
            "mounted" => self.mounted = Some(ImmutableProperty::from_raw(raw)?),
            "mountpoint" => self.mountpoint = Some(MutableProperty::from_raw(raw)?),
            "readonly" => self.readonly = Some(MutableProperty::from_raw(raw)?),
            "redundant_metadata" => self.redundant_metadata = Some(MutableProperty::from_raw(raw)?),
            "refcompressratio" => self.refcompressratio = Some(ImmutableProperty::from_raw(raw)?),
            "referenced" => self.referenced = Some(ImmutableProperty::from_raw(raw)?),
            "refquota" => self.refquota = Some(MutableProperty::from_raw(raw)?),
            "relatime" => self.relatime = Some(MutableProperty::from_raw(raw)?),
            "quota" => self.quota = Some(MutableProperty::from_raw(raw)?),
            "sharenfs" => self.sharenfs = Some(MutableProperty::from_raw(raw)?),
            "snapshot_count" => self.snapshot_count = Some(MutableProperty::from_raw(raw)?),
            "snapshot_limit" => self.snapshot_limit = Some(MutableProperty::from_raw(raw)?),
            "sync" => self.sync = Some(MutableProperty::from_raw(raw)?),
            "type" => self.type_ = Some(ImmutableProperty::from_raw(raw)?),
            "used" => self.used = Some(ImmutableProperty::from_raw(raw)?),
            "usedbychildren" => self.usedbychildren = Some(ImmutableProperty::from_raw(raw)?),
            "usedbydataset" => self.usedbydataset = Some(ImmutableProperty::from_raw(raw)?),
            "usedbyrefreservation" => {
                self.usedbyrefreservation = Some(ImmutableProperty::from_raw(raw)?);
            }
            "usedbysnapshots" => self.usedbysnapshots = Some(ImmutableProperty::from_raw(raw)?),
            "version" => self.version = Some(ImmutableProperty::from_raw(raw)?),
            "volmode" => self.volmode = Some(MutableProperty::from_raw(raw)?),
            "written" => self.written = Some(ImmutableProperty::from_raw(raw)?),
            _ => {
                trace!("failed to match raw property name {}", raw.name);
            }
        }
        Ok(())
    }

    fn fix_name(name: &str, root: &str) -> String {
        let root_len = root.len();
        if name.len() == root_len {
            "/".to_string()
        } else {
            name[root_len..].to_string()
        }
    }

    pub fn fix_dataset_relative(&mut self, root: &str) {
        self.name = Self::fix_name(&self.name, root);
    }

    pub fn fix_snapshot_relative(&mut self, root: &str) -> Result<String, PropertyError> {
        let name = self.name.clone();
        let (parent, child) = name
            .split_once('@')
            .ok_or_else(|| PropertyError::MissingAt { name: name.clone() })?;
        self.name = child.to_string();
        Ok(Self::fix_name(parent, root))
    }

    pub fn from_raws(raw: &str) -> Result<IndexMap<String, Self>, PropertyError> {
        let raw_properties: Vec<RawProperty> = RawProperty::from_raws(raw)?;
        let mut descriptions: IndexMap<String, Self> = IndexMap::new();
        for raw_property in raw_properties {
            let name: &String = &raw_property.dataset;
            let item = descriptions.get_mut(name);
            match item {
                None => {
                    let mut description = Self::new(name.clone());
                    description.fill(&raw_property)?;
                    descriptions.insert(name.clone(), description);
                }
                Some(value) => {
                    value.fill(&raw_property)?;
                }
            }
        }
        Ok(descriptions)
    }
}
