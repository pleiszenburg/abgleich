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
from .property import Property
from ..command import Command

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

    def __getitem__(self, name: str) -> PropertyABC:

        return self._properties[name]

    @property
    def name(self) -> str:

        return self._name

    @property
    def parent(self) -> str:

        return self._parent

    @classmethod
    def from_line(cls, line: str, side: str, config: typing.Dict) -> SnapshotABC:

        name = line.split('\t')[0]

        output, _ = Command.on_side(["zfs", "get", "all", "-H", "-p", name], side, config).run()
        properties = {property.name: property for property in (
            Property.from_line(line)
            for line in output.split('\n')
            if len(line.strip()) > 0
            )}

        parent, name = name.split('@')

        return cls(
            name = name,
            parent = parent,
            properties = properties,
            side = side,
            config = config,
        )
