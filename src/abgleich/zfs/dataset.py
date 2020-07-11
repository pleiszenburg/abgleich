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
from .property import Property
from .snapshot import Snapshot
from ..command import Command

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

    @property
    def snapshots(self) -> typing.Generator[SnapshotABC, None, None]:

        return (snapshot for snapshot in self._snapshots)

    @classmethod
    def from_line(cls, line: str, side: str, config: typing.Dict) -> DatasetABC:

        name = line.split('\t')[0]

        output, _ = Command.on_side(["zfs", "get", "all", "-H", "-p", name], side, config).run()
        properties = {property.name: property for property in (
            Property.from_line(line)
            for line in output.split('\n')
            if len(line.strip()) > 0
            )}

        output, _ = Command.on_side(["zfs", "list", "-t", "snapshot", "-H", "-p", name], side, config).run()
        snapshots = [
            Snapshot.from_line(line, side, config)
            for line in output.split('\n')
            if len(line.strip()) > 0
            ]

        return cls(
            name = name,
            properties = properties,
            snapshots = snapshots,
            side = side,
            config = config,
        )
