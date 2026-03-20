use indexmap::IndexMap;
use tracing::trace;

use super::errors::EngineError;
use super::property::{Property, RawProperty};

pub struct Meta {
    pub abgleich_diff: Property,
    pub abgleich_format: Property,
    pub abgleich_overlap: Property,
    pub abgleich_snap: Property,
    pub abgleich_sync: Property,
    pub abgleich_threshold: Property,
    pub atime: Property,
    pub available: Property,
    pub canmount: Property,
    pub checksum: Property,
    pub compression: Property,
    pub compressratio: Property,
    pub creation: Property,
    pub dedup: Property,
    pub encryption: Property,
    pub filesystem_count: Property,
    pub filesystem_limit: Property,
    pub guid: Property,
    pub logicalreferenced: Property,
    pub logicalused: Property,
    pub mounted: Property,
    pub mountpoint: Property,
    pub name: String,
    pub readonly: Property,
    pub redundant_metadata: Property,
    pub refcompressratio: Property,
    pub referenced: Property,
    pub refquota: Property,
    pub relatime: Property,
    pub quota: Property,
    pub sharenfs: Property,
    pub snapshot_count: Property,
    pub snapshot_limit: Property,
    pub sync: Property,
    pub type_: Property,
    pub used: Property,
    pub usedbychildren: Property,
    pub usedbydataset: Property,
    pub usedbyrefreservation: Property,
    pub usedbysnapshots: Property,
    pub version: Property,
    pub volmode: Property,
    pub written: Property,
}

impl Meta {
    pub fn new(name: &str) -> Self {
        Self {
            abgleich_diff: Property::empty_bool(true),
            abgleich_format: Property::empty_string(true),
            abgleich_overlap: Property::empty_int(true),
            abgleich_snap: Property::empty_snap(true),
            abgleich_sync: Property::empty_bool(true),
            abgleich_threshold: Property::empty_uint(true),
            atime: Property::empty_bool(true),
            available: Property::empty_int(false),
            canmount: Property::empty_bool(true),
            checksum: Property::empty_bool(true),
            compression: Property::empty_string(true),
            compressratio: Property::empty_float(false),
            creation: Property::empty_int(false),
            dedup: Property::empty_bool(true),
            encryption: Property::empty_bool(true),
            filesystem_count: Property::empty_uint(true),
            filesystem_limit: Property::empty_uint(true),
            guid: Property::empty_uint(false),
            logicalreferenced: Property::empty_uint(false),
            logicalused: Property::empty_uint(false),
            mounted: Property::empty_bool(false),
            mountpoint: Property::empty_string(true),
            name: name.to_string(),
            readonly: Property::empty_bool(true),
            redundant_metadata: Property::empty_string(true),
            refcompressratio: Property::empty_float(false),
            referenced: Property::empty_uint(false),
            refquota: Property::empty_uint(true),
            relatime: Property::empty_bool(true),
            quota: Property::empty_uint(true),
            sharenfs: Property::empty_bool(true),
            snapshot_count: Property::empty_uint(true),
            snapshot_limit: Property::empty_uint(true),
            sync: Property::empty_string(true),
            type_: Property::empty_type(false),
            used: Property::empty_uint(false),
            usedbychildren: Property::empty_uint(false),
            usedbydataset: Property::empty_uint(false),
            usedbyrefreservation: Property::empty_uint(false),
            usedbysnapshots: Property::empty_uint(false),
            version: Property::empty_uint(false),
            volmode: Property::empty_string(true),
            written: Property::empty_uint(false),
        }
    }

    pub fn get_property_mut_ref(&mut self, name: &str) -> Result<&mut Property, EngineError> {
        Ok(match name {
            "abgleich:diff" => &mut self.abgleich_diff,
            "abgleich:format" => &mut self.abgleich_format,
            "abgleich:overlap" => &mut self.abgleich_overlap,
            "abgleich:snap" => &mut self.abgleich_snap,
            "abgleich:sync" => &mut self.abgleich_sync,
            "abgleich:threshold" => &mut self.abgleich_threshold,
            "atime" => &mut self.atime,
            "available" => &mut self.available,
            "canmount" => &mut self.canmount,
            "checksum" => &mut self.checksum,
            "compression" => &mut self.compression,
            "compressratio" => &mut self.compressratio,
            "creation" => &mut self.creation,
            "dedup" => &mut self.dedup,
            "encryption" => &mut self.encryption,
            "filesystem_count" => &mut self.filesystem_count,
            "filesystem_limit" => &mut self.filesystem_limit,
            "guid" => &mut self.guid,
            "logicalreferenced" => &mut self.logicalreferenced,
            "logicalused" => &mut self.logicalused,
            "mounted" => &mut self.mounted,
            "mountpoint" => &mut self.mountpoint,
            "readonly" => &mut self.readonly,
            "redundant_metadata" => &mut self.redundant_metadata,
            "refcompressratio" => &mut self.refcompressratio,
            "referenced" => &mut self.referenced,
            "refquota" => &mut self.refquota,
            "relatime" => &mut self.relatime,
            "quota" => &mut self.quota,
            "sharenfs" => &mut self.sharenfs,
            "snapshot_count" => &mut self.snapshot_count,
            "snapshot_limit" => &mut self.snapshot_limit,
            "sync" => &mut self.sync,
            "type" => &mut self.type_,
            "used" => &mut self.used,
            "usedbychildren" => &mut self.usedbychildren,
            "usedbydataset" => &mut self.usedbydataset,
            "usedbyrefreservation" => &mut self.usedbyrefreservation,
            "usedbysnapshots" => &mut self.usedbysnapshots,
            "version" => &mut self.version,
            "volmode" => &mut self.volmode,
            "written" => &mut self.written,
            _ => {
                trace!("failed to match raw property name {}", name);
                return Err(EngineError::PropertyUnknownError);
            }
        })
    }

    pub fn fill(&mut self, raw_property: &RawProperty) -> Result<(), EngineError> {
        match self.get_property_mut_ref(&raw_property.name) {
            Ok(property) => property.set_raw(raw_property),
            Err(error) => match error {
                EngineError::PropertyUnknownError => Ok(()),
                _ => Err(error),
            },
        }
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

    pub fn fix_snapshot_relative(&mut self, root: &str) -> String {
        let name = self.name.clone();
        let (parent, child) = name.split_once('@').unwrap(); // safe unwrap
        self.name = child.to_string();
        Self::fix_name(parent, root)
    }

    pub fn from_raws(raw: &str) -> Result<IndexMap<String, Self>, EngineError> {
        let raw_properties: Vec<RawProperty> = RawProperty::from_raws(raw)?;
        let mut metas: IndexMap<String, Self> = IndexMap::new();
        for raw_property in raw_properties {
            let name: &String = &raw_property.dataset;
            let item = metas.get_mut(name);
            match item {
                None => {
                    let mut meta = Self::new(name);
                    meta.fill(&raw_property)?;
                    metas.insert(name.clone(), meta);
                }
                Some(value) => {
                    value.fill(&raw_property)?;
                }
            }
        }
        Ok(metas)
    }
}
