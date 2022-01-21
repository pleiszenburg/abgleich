# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/core/dataset.py: ZFS dataset

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

import datetime
from typing import Dict, Generator, List, Union

# Python <= 3.7.1 "fix"
try:
    from typing import OrderedDict as DictType
except ImportError:
    DictType = Dict

from typeguard import typechecked

from .abc import ConfigABC, DatasetABC, PropertyABC, SnapshotABC, TransactionListABC
from .command import Command
from .i18n import t
from .lib import root
from .property import Property
from .transaction import Transaction
from .transactionlist import TransactionList
from .transactionmeta import TransactionMeta
from .snapshot import Snapshot

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@typechecked
class Dataset(DatasetABC):
    """
    Immutable.
    """

    def __init__(
        self,
        name: str,
        properties: Dict[str, PropertyABC],
        snapshots: List[SnapshotABC],
        side: str,
        config: ConfigABC,
    ):

        self._name = name
        self._properties = properties
        self._snapshots = snapshots
        self._side = side
        self._config = config

        self._root = root(
            config[f"{side:s}/zpool"].value, config[f"{side:s}/prefix"].value
        )

        assert self._name.startswith(self._root)
        self._subname = self._name[len(self._root) :].strip("/")

    def __eq__(self, other: DatasetABC) -> bool:

        return self.subname == other.subname

    def __len__(self) -> int:

        return len(self._snapshots)

    def __getitem__(self, key: Union[str, int, slice]) -> PropertyABC:

        if isinstance(key, str):
            return self._properties[key]
        return self._snapshots[key]

    def get(
        self,
        key: Union[str, int, slice],
        default: Union[None, PropertyABC] = None,
    ) -> Union[None, PropertyABC]:

        if isinstance(key, str):
            return self._properties.get(
                key,
                Property(key, None, None) if default is None else default,
            )

        assert isinstance(key, int) or isinstance(key, slice)

        try:
            return self._snapshots[key]
        except IndexError:
            return default

    @property
    def changed(self) -> bool:

        if len(self) == 0:
            return True
        if self._config["always_changed"].value:
            return True

        if self._config["compatibility/tagging"].value:
            if self._snapshots[-1].get("abgleich:type").value != "backup":
                return True

        if self._properties["written"].value == 0:
            return False
        if self._properties["type"].value == "volume":
            return True

        if self._config["written_threshold"].value is not None:
            if (
                self._properties["written"].value
                > self._config["written_threshold"].value
            ):
                return True

        if not self._config["check_diff"].value:
            return True

        output, _ = (
            Command.from_list(
                ["zfs", "diff", f"{self._name:s}@{self._snapshots[-1].name:s}"]
            )
            .on_side(side=self._side, config=self._config)
            .run()
        )
        return len(output[0].strip(" \t\n")) > 0

    @property
    def ignore(self) -> bool:

        return self._subname in self._config["ignore"].value

    @property
    def name(self) -> str:

        return self._name

    @property
    def subname(self) -> str:

        return self._subname

    @property
    def snapshots(self) -> Generator[SnapshotABC, None, None]:

        return (snapshot for snapshot in self._snapshots)

    @property
    def root(self) -> str:

        return self._root

    def get_snapshot_transactions(self) -> TransactionListABC:

        snapshot_name = self._new_snapshot_name()

        command = ["zfs", "snapshot"]
        if self._config["compatibility/tagging"].value:
            command.extend(["-o", "abgleich:type=backup"])
        command.append(f"{self._name:s}@{snapshot_name:s}")

        return TransactionList(
            Transaction(
                meta=TransactionMeta(
                    **{
                        t("type"): t("snapshot"),
                        t("dataset_subname"): self._subname,
                        t("snapshot_name"): snapshot_name,
                        t("written"): self._properties["written"].value,
                    }
                ),
                command=Command.from_list(command).on_side(
                    side=self._side, config=self._config
                ),
            )
        )

    def _new_snapshot_name(self) -> str:

        today = datetime.datetime.now().strftime("%Y%m%d")
        max_snapshots = (10 ** self._config["digits"].value) - 1
        suffix = (
            self._config["suffix"].value
            if self._config["suffix"].value is not None
            else ""
        )

        todays_names = [
            snapshot.name
            for snapshot in self._snapshots
            if all(
                (
                    snapshot.name.startswith(today),
                    snapshot.name.endswith(suffix),
                    len(snapshot.name)
                    == len(today) + self._config["digits"].value + len(suffix),
                )
            )
        ]
        todays_numbers = [
            int(name[len(today) : len(today) + self._config["digits"].value])
            for name in todays_names
            if name[len(today) : len(today) + self._config["digits"].value].isnumeric()
        ]
        if len(todays_numbers) != 0:
            todays_numbers.sort()
            new_number = todays_numbers[-1] + 1
            if new_number > max_snapshots:
                raise ValueError(f"more than {max_snapshots:d} snapshots per day")
        else:
            new_number = 1

        return f"{today:s}{new_number:02d}{suffix}"

    @classmethod
    def from_entities(
        cls,
        name: str,
        entities: DictType[str, List[List[str]]],
        side: str,
        config: ConfigABC,
    ) -> DatasetABC:

        properties = {
            property.name: property
            for property in (Property.from_params(*params) for params in entities[name])
        }
        entities.pop(name)

        snapshots = []
        snapshots.extend(
            (
                Snapshot.from_entity(
                    snapshot_name,
                    entities[snapshot_name],
                    snapshots,
                    side,
                    config,
                )
                for snapshot_name in entities.keys()
            )
        )

        return cls(
            name=name,
            properties=properties,
            snapshots=snapshots,
            side=side,
            config=config,
        )
