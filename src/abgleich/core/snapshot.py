# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/core/snapshot.py: ZFS snapshot

    Copyright (C) 2019-2022 Sebastian M. Ernst <ernst@pleiszenburg.de>

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

from typing import Dict, List, Union

from typeguard import typechecked

from .abc import ConfigABC, PropertyABC, SnapshotABC, TransactionABC, TransactionListABC
from .command import Command
from .i18n import t
from .lib import root
from .property import Property
from .transaction import Transaction
from .transactionlist import TransactionList
from .transactionmeta import TransactionMeta

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@typechecked
class Snapshot(SnapshotABC):
    """
    Immutable.
    """

    def __init__(
        self,
        name: str,
        parent: str,
        properties: Dict[str, PropertyABC],
        context: List[SnapshotABC],
        side: str,
        config: ConfigABC,
    ):

        self._name = name
        self._parent = parent
        self._properties = properties
        self._context = context
        self._side = side
        self._config = config

        self._root = root(
            config[f"{side:s}/zpool"].value, config[f"{side:s}/prefix"].value
        )

        assert self._parent.startswith(self._root)
        self._subparent = self._parent[len(self._root) :].strip("/")

        self._intermediates = []  # for namespaces / tagging

    def __eq__(self, other: SnapshotABC) -> bool:

        return self.subparent == other.subparent and self.name == other.name

    def __getitem__(self, name: str) -> PropertyABC:

        return self._properties[name]

    def get(
        self,
        key: str,
        default: Union[None, PropertyABC] = None,
    ) -> Union[None, PropertyABC]:

        return self._properties.get(
            key,
            Property(key, None, None) if default is None else default,
        )

    def get_cleanup_transactions(self) -> TransactionListABC:

        return TransactionList(
            Transaction(
                meta=TransactionMeta(
                    **{
                        t("type"): t("cleanup_snapshot"),
                        t("snapshot_subparent"): self._subparent,
                        t("snapshot_name"): self._name,
                    }
                ),
                command=Command.from_list(
                    ["zfs", "destroy", f"{self._parent:s}@{self._name:s}"]
                ).on_side(side=self._side, config=self._config),
            )
        )

    def get_backup_transactions(
        self,
        source_dataset: str,
        target_dataset: str,
    ) -> TransactionListABC:

        assert self._side == "source"

        ancestor = self.ancestor

        send = Command.from_list(
            [
                "zfs",
                "send",
                "-c",
                f"{source_dataset:s}@{self.name:s}",
            ]
            if ancestor is None
            else [
                "zfs",
                "send",
                "-c",
                "-i",
                f"{source_dataset:s}@{ancestor.name:s}",
                f"{source_dataset:s}@{self.name:s}",
            ]
        )
        receive = Command.from_list(["zfs", "receive", f"{target_dataset:s}"])

        if self._config["source/processing"].set:
            send = send | Command.from_str(self._config["source/processing"].value)
        if self._config["target/processing"].set:
            receive = (
                Command.from_str(self._config["target/processing"].value) | receive
            )

        command = send.on_side(side="source", config=self._config) | receive.on_side(
            side="target", config=self._config
        )

        transactions = TransactionList(
            Transaction(
                meta=TransactionMeta(
                    **{
                        t("type"): t("transfer_snapshot")
                        if ancestor is None
                        else t("transfer_snapshot_incremental"),
                        t("snapshot_subparent"): self._subparent,
                        t("ancestor_name"): "" if ancestor is None else ancestor.name,
                        t("snapshot_name"): self.name,
                    }
                ),
                command=command,
            )
        )

        if self._config["compatibility/tagging"].value:
            transactions.append(
                Transaction.set_property(
                    item=f"{target_dataset:s}@{self.name:s}",
                    property=Property(name="abgleich:type", value="backup"),
                    side="target",
                    config=self._config,
                )
            )

        return transactions

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
    def ancestor(self) -> Union[None, SnapshotABC]:

        assert self in self._context
        self_index = self._context.index(self)

        if self_index == 0:
            return None
        return self._context[self_index - 1]

    @property
    def root(self) -> str:

        return self._root

    @property
    def intermediates(self) -> List[SnapshotABC]:

        return self._intermediates

    @classmethod
    def from_entity(
        cls,
        name: str,
        entity: List[List[str]],
        context: List[SnapshotABC],
        side: str,
        config: ConfigABC,
    ) -> SnapshotABC:

        properties = {
            property.name: property
            for property in (Property.from_params(*params) for params in entity)
        }

        parent, name = name.split("@")

        return cls(
            name=name,
            parent=parent,
            properties=properties,
            context=context,
            side=side,
            config=config,
        )
