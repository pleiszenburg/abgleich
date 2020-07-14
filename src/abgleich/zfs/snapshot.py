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

from .abc import PropertyABC, SnapshotABC, TransactionABC
from .lib import root
from .property import Property
from .transaction import Transaction, TransactionMeta
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
        context: typing.List[SnapshotABC],
        side: str,
        config: typing.Dict,
        ):

        self._name = name
        self._parent = parent
        self._properties = properties
        self._context = context
        self._side = side
        self._config = config

        self._root = root(config[side]['zpool'], config[side]['prefix'])

        assert self._parent.startswith(self._root)
        self._subparent = self._parent[len(self._root):].strip('/')

    def __eq__(self, other: SnapshotABC) -> bool:

        return self.subparent == other.subparent and self.name == other.name

    def __getitem__(self, name: str) -> PropertyABC:

        return self._properties[name]

    def get_backup_transaction(
        self,
        source_dataset: str,
        target_dataset: str,
    ) -> TransactionABC:

        ancestor = self.ancestor

        commands = [
            Command.on_side(
            [
                "zfs", "send", "-c",
                f"{source_dataset:s}@{self.name:s}",
            ] if ancestor is None else [
                "zfs", "send", "-c", "-i",
                f"{source_dataset:s}@%{ancestor.name:s}",
                f"{source_dataset:s}@%{self.name:s}",
            ],
            'source', self._config
            ),
            Command.on_side(
            [
                "zfs", "receive", f"{target_dataset:s}"
            ],
            'target', self._config
            ),
        ]

        return Transaction(
            meta = TransactionMeta(
                type = 'push_snapshot' if ancestor is None else 'push_snapshot_incremental',
                snapshot_subparent = self._subparent,
                ancestor_name = "" if ancestor is None else ancestor.name,
                snapshot_name = self.name,
                ),
            commands = commands,
            )

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
    def ancestor(self) -> typing.Union[None, SnapshotABC]:

        assert self in self._context
        self_index = self._context.index(self)

        if self_index == 0:
            return None
        return self._context[self_index - 1]

    @property
    def root(self) -> str:

        return self._root

    @classmethod
    def from_entity(
        cls,
        name: str,
        entity: typing.List[typing.List[str]],
        context: typing.List[SnapshotABC],
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
            context = context,
            side = side,
            config = config,
        )
