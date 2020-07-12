# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/zfs/dataset.py: ZFS dataset

    Copyright (C) 2019-2020 Sebastian M. Ernst <ernst@pleiszenburg.de>

<LICENSE_BLOCK>
The contents of this file are subject to the GNU Lesser General Public License
Version 2.1 ("LGPL" or "License"). You may not use this file except in
compliance with the License. You may obtain a copy of the License at
https://www.gnu.org/licenses/old-licenses/lgpl-2.1.txt
https://github.com/pleiszenburg/abgleich/blob/master/LICENSE

Software distributed under the License is distributed on an "AS IS" basis,
WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License for the
specific language governing rights and limitations under the License.
</LICENSE_BLOCK>

"""

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# IMPORT
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import typing

import typeguard

from .abc import DatasetABC, PropertyABC, SnapshotABC
from .lib import join
from .property import Property
from .snapshot import Snapshot

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@typeguard.typechecked
class Dataset(DatasetABC):

    def __init__(self,
        name: str,
        properties: typing.Dict[str, PropertyABC],
        snapshots: typing.List[SnapshotABC],
        side: str,
        config: typing.Dict,
        ):

        self._name = name
        self._properties = properties
        self._snapshots = snapshots
        self._side = side
        self._config = config

        root = config[side]['zpool']
        if config[side]['prefix'] is not None:
            root = join(root, config[side]['prefix'])
        assert self._name.startswith(root)
        self._subname = self._name[len(root):]

    def __eq__(self, other: DatasetABC) -> bool:

        return self.subname == other.subname

    def __len__(self) -> int:

        return len(self._snapshots)

    def __getitem__(self, key: typing.Union[str, int, slice]) -> PropertyABC:

        if isinstance(key, str):
            return self._properties[key]
        return self._snapshots[key]

    @property
    def name(self) -> str:

        return self._name

    @property
    def subname(self) -> str:

        return self._subname

    @property
    def snapshots(self) -> typing.Generator[SnapshotABC, None, None]:

        return (snapshot for snapshot in self._snapshots)

    @classmethod
    def from_entities(cls,
        name: str,
        entities: typing.Dict[str, typing.List[typing.List[str]]],
        side: str,
        config: typing.Dict,
        ) -> DatasetABC:

        properties = {property.name: property for property in (
            Property.from_params(*params)
            for params in entities[name]
            )}
        entities.pop(name)

        snapshots = [
            Snapshot.from_entity(
                snapshot_name,
                entities[snapshot_name],
                side,
                config,
                )
            for snapshot_name in entities.keys()
            ]
        snapshots.sort(key = lambda snapshot: snapshot['creation'].value)

        return cls(
            name = name,
            properties = properties,
            snapshots = snapshots,
            side = side,
            config = config,
            )
