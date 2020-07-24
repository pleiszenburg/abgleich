# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/core/dataset.py: ZFS dataset

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

import datetime
import typing

# Python <= 3.7.1 "fix"
try:
    from typing import OrderedDict as DictType
except ImportError:
    from typing import Dict as DictType

import typeguard

from .abc import ConfigABC, DatasetABC, PropertyABC, TransactionABC, SnapshotABC
from .command import Command
from .i18n import t
from .lib import root
from .property import Property
from .transaction import Transaction, TransactionMeta
from .snapshot import Snapshot

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@typeguard.typechecked
class Dataset(DatasetABC):
    def __init__(
        self,
        name: str,
        properties: typing.Dict[str, PropertyABC],
        snapshots: typing.List[SnapshotABC],
        side: str,
        config: ConfigABC,
    ):

        self._name = name
        self._properties = properties
        self._snapshots = snapshots
        self._side = side
        self._config = config

        self._root = root(config[side]["zpool"], config[side]["prefix"])

        assert self._name.startswith(self._root)
        self._subname = self._name[len(self._root) :].strip("/")

    def __eq__(self, other: DatasetABC) -> bool:

        return self.subname == other.subname

    def __len__(self) -> int:

        return len(self._snapshots)

    def __getitem__(self, key: typing.Union[str, int, slice]) -> PropertyABC:

        if isinstance(key, str):
            return self._properties[key]
        return self._snapshots[key]

    def get(
        self,
        key: typing.Union[str, int, slice],
        default: typing.Union[None, PropertyABC] = None,
    ) -> typing.Union[None, PropertyABC]:

        if isinstance(key, str):
            return self._properties.get(
                key, Property(key, None, None) if default is None else default,
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
        if self._config["always_changed"]:
            return True
        if self._properties["written"].value == 0:
            return False
        if self._properties["type"].value == "volume":
            return True

        if self._config["written_threshold"] is not None:
            if self._properties["written"].value > self._config["written_threshold"]:
                return True

        if not self._config["check_diff"]:
            return True

        output, _ = Command.on_side(
            ["zfs", "diff", f"{self._name:s}@{self._snapshots[-1].name:s}"],
            self._side,
            self._config,
        ).run()
        return len(output.strip(" \t\n")) > 0

    @property
    def name(self) -> str:

        return self._name

    @property
    def subname(self) -> str:

        return self._subname

    @property
    def snapshots(self) -> typing.Generator[SnapshotABC, None, None]:

        return (snapshot for snapshot in self._snapshots)

    @property
    def root(self) -> str:

        return self._root

    def get_snapshot_transaction(self) -> TransactionABC:

        snapshot_name = self._new_snapshot_name()

        return Transaction(
            TransactionMeta(
                **{
                    t("type"): t("snapshot"),
                    t("dataset_subname"): self._subname,
                    t("snapshot_name"): snapshot_name,
                    t("written"): self._properties["written"].value,
                }
            ),
            [
                Command.on_side(
                    ["zfs", "snapshot", f"{self._name:s}@{snapshot_name:s}"],
                    self._side,
                    self._config,
                )
            ],
        )

    def _new_snapshot_name(self) -> str:

        today = datetime.datetime.now().strftime("%Y%m%d")
        max_snapshots = (10 ** self._config["digits"]) - 1
        suffix = self._config["suffix"] if self._config["suffix"] is not None else ""

        todays_names = [
            snapshot.name
            for snapshot in self._snapshots
            if all(
                (
                    snapshot.name.startswith(today),
                    snapshot.name.endswith(suffix),
                    len(snapshot.name)
                    == len(today) + self._config["digits"] + len(suffix),
                )
            )
        ]
        todays_numbers = [
            int(name[len(today) : len(today) + self._config["digits"]])
            for name in todays_names
            if name[len(today) : len(today) + self._config["digits"]].isnumeric()
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
        entities: DictType[str, typing.List[typing.List[str]]],
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
                    snapshot_name, entities[snapshot_name], snapshots, side, config,
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
