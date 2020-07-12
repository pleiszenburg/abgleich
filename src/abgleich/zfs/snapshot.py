# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/zfs/snapshot.py: ZFS snapshot

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

from .abc import PropertyABC, SnapshotABC
from .lib import join
from .property import Property

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@typeguard.typechecked
class Snapshot(SnapshotABC):

    def __init__(self,
        name: str,
        parent: str,
        properties: typing.Dict[str, PropertyABC],
        side: str,
        config: typing.Dict,
        ):

        self._name = name
        self._parent = parent
        self._properties = properties
        self._side = side
        self._config = config

        root = config[side]['zpool']
        if config[side]['prefix'] is not None:
            root = join(root, config[side]['prefix'])
        assert self._parent.startswith(root)
        self._subparent = self._parent[len(root):].strip('/')

    def __eq__(self, other: SnapshotABC) -> bool:

        return self.subparent == other.subparent

    def __getitem__(self, name: str) -> PropertyABC:

        return self._properties[name]

    @property
    def name(self) -> str:

        return self._name

    @property
    def parent(self) -> str:

        return self._parent

    @property
    def subparent(self) -> str:

        return self._subparent

    @property
    def sortkey(self) -> int:

        return self._properties['creation'].value

    @classmethod
    def from_entity(
        cls,
        name: str,
        entity: typing.List[typing.List[str]],
        side: str,
        config: typing.Dict,
        ) -> SnapshotABC:

        properties = {property.name: property for property in (
            Property.from_params(*params)
            for params in entity
            )}

        parent, name = name.split('@')

        return cls(
            name = name,
            parent = parent,
            properties = properties,
            side = side,
            config = config,
        )
