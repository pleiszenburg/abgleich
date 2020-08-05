# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/core/zpool.py: ZFS zpool

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

from collections import OrderedDict
import typing

from tabulate import tabulate
import typeguard

from .abc import (
    ComparisonItemABC,
    ConfigABC,
    DatasetABC,
    SnapshotABC,
    TransactionABC,
    TransactionListABC,
    ZpoolABC,
)
from .command import Command
from .comparison import Comparison
from .dataset import Dataset
from .i18n import t
from .io import colorize, humanize_size
from .lib import join, root
from .property import Property
from .transaction import TransactionList

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@typeguard.typechecked
class Zpool(ZpoolABC):
    def __init__(
        self, datasets: typing.List[DatasetABC], side: str, config: ConfigABC,
    ):

        self._datasets = datasets
        self._side = side
        self._config = config

        self._root = root(config[side]["zpool"], config[side]["prefix"])

    def __eq__(self, other: ZpoolABC) -> bool:

        return self.side == other.side

    @property
    def datasets(self) -> typing.Generator[DatasetABC, None, None]:

        return (dataset for dataset in self._datasets)

    @property
    def side(self) -> str:

        return self._side

    @property
    def root(self) -> str:

        return self._root

    def get_cleanup_transactions(self, other: ZpoolABC,) -> TransactionListABC:

        assert self.side == "source"
        assert other.side == "target"

        zpool_comparison = Comparison.from_zpools(self, other)
        transactions = TransactionList()

        for dataset_item in zpool_comparison.merged:

            cleanup_transactions = self._get_cleanup_from_datasetitem(dataset_item)
            if cleanup_transactions is None:
                continue
            transactions.extend(cleanup_transactions)

        return transactions

    def generate_cleanup_transactions(
        self, other: ZpoolABC,
    ) -> typing.Generator[
        typing.Tuple[
            int,
            typing.Union[
                None, typing.Union[None, typing.Generator[TransactionABC, None, None]]
            ],
        ],
        None,
        None,
    ]:

        assert self.side == "source"
        assert other.side == "target"

        zpool_comparison = Comparison.from_zpools(self, other)

        yield len(zpool_comparison), None

        for index, dataset_item in enumerate(zpool_comparison.merged):
            yield index, self._get_cleanup_from_datasetitem(dataset_item)

    def _get_cleanup_from_datasetitem(
        self, dataset_item: ComparisonItemABC,
    ) -> typing.Union[None, typing.Generator[TransactionABC, None, None]]:

        if dataset_item.get_item().subname in self._config["ignore"]:
            return
        if dataset_item.a is None or dataset_item.b is None:
            return

        dataset_comparison = Comparison.from_datasets(dataset_item.a, dataset_item.b)
        snapshots = dataset_comparison.a_overlap_tail[: -self._config["keep_snapshots"]]

        return (snapshot.get_cleanup_transaction() for snapshot in snapshots)

    def get_backup_transactions(self, other: ZpoolABC,) -> TransactionListABC:

        assert self.side == "source"
        assert other.side == "target"

        zpool_comparison = Comparison.from_zpools(self, other)
        transactions = TransactionList()

        for dataset_item in zpool_comparison.merged:
            backup_transactions = self._get_backup_transactions_from_datasetitem(
                other, dataset_item
            )
            if backup_transactions is None:
                continue
            transactions.extend(backup_transactions)

        return transactions

    def generate_backup_transactions(
        self, other: ZpoolABC,
    ) -> typing.Generator[
        typing.Tuple[
            int,
            typing.Union[
                None, typing.Union[None, typing.Generator[TransactionABC, None, None]]
            ],
        ],
        None,
        None,
    ]:

        assert self.side == "source"
        assert other.side == "target"

        zpool_comparison = Comparison.from_zpools(self, other)

        yield len(zpool_comparison), None

        for index, dataset_item in enumerate(zpool_comparison.merged):
            yield index, self._get_backup_transactions_from_datasetitem(
                other, dataset_item
            )

    def _get_backup_transactions_from_datasetitem(
        self, other: ZpoolABC, dataset_item: ComparisonItemABC,
    ) -> typing.Union[None, typing.Generator[TransactionABC, None, None]]:

        if dataset_item.get_item().subname in self._config["ignore"]:
            return
        if dataset_item.a is None:
            return

        if dataset_item.b is None:
            snapshots = list(dataset_item.a.snapshots)
        else:
            dataset_comparison = Comparison.from_datasets(
                dataset_item.a, dataset_item.b
            )
            snapshots = dataset_comparison.a_head

        if len(snapshots) == 0:
            return

        source_dataset = (
            self.root
            if len(dataset_item.a.subname) == 0
            else join(self.root, dataset_item.a.subname)
        )
        target_dataset = (
            other.root
            if len(dataset_item.a.subname) == 0
            else join(other.root, dataset_item.a.subname)
        )

        return (
            snapshot.get_backup_transaction(source_dataset, target_dataset,)
            for snapshot in snapshots
        )

    def get_snapshot_transactions(self) -> TransactionListABC:

        assert self._side == "source"

        transactions = TransactionList()

        for dataset in self._datasets:
            transaction = self._get_snapshot_transactions_from_dataset(dataset)
            if transaction is None:
                continue
            transactions.append(dataset.get_snapshot_transaction())

        return transactions

    def generate_snapshot_transactions(
        self,
    ) -> typing.Generator[
        typing.Tuple[int, typing.Union[None, TransactionABC]], None, None
    ]:

        assert self._side == "source"

        yield len(self._datasets), None

        for index, dataset in enumerate(self._datasets):
            yield index, self._get_snapshot_transactions_from_dataset(dataset)

    def _get_snapshot_transactions_from_dataset(
        self, dataset: DatasetABC
    ) -> typing.Union[None, TransactionABC]:

        if dataset.subname in self._config["ignore"]:
            return
        if (
            dataset.get("mountpoint").value is None
            and dataset["type"].value == "filesystem"
        ):
            return
        if not dataset.changed:
            return

        return dataset.get_snapshot_transaction()

    def print_table(self):

        table = []
        for dataset in self._datasets:
            table.append(self._table_row(dataset))
            for snapshot in dataset.snapshots:
                table.append(self._table_row(snapshot))

        if len(table) == 0:
            print('(empty)')
            return

        print(
            tabulate(
                table,
                headers=(t("NAME"), t("USED"), t("REFER"), t("compressratio")),
                tablefmt="github",
                colalign=("left", "right", "right", "decimal"),
            )
        )

    @staticmethod
    def _table_row(entity: typing.Union[SnapshotABC, DatasetABC]) -> typing.List[str]:

        return [
            "- " + colorize(entity.name, "grey")
            if isinstance(entity, SnapshotABC)
            else colorize(entity.name, "white"),
            humanize_size(entity["used"].value, add_color=True),
            humanize_size(entity["referenced"].value, add_color=True),
            f'{entity["compressratio"].value:.02f}',
        ]

    def print_comparison_table(self, other: ZpoolABC):

        zpool_comparison = Comparison.from_zpools(self, other)
        table = []

        for dataset_item in zpool_comparison.merged:
            table.append(self._comparison_table_row(dataset_item))
            if dataset_item.complete:
                dataset_comparison = Comparison.from_datasets(
                    dataset_item.a, dataset_item.b
                )
            elif dataset_item.a is not None:
                dataset_comparison = Comparison.from_datasets(dataset_item.a, None)
            else:
                dataset_comparison = Comparison.from_datasets(None, dataset_item.b)
            for snapshot_item in dataset_comparison.merged:
                table.append(self._comparison_table_row(snapshot_item))

        print(
            tabulate(
                table,
                headers=[t("NAME"), t(self.side), t(other.side)],
                tablefmt="github",
            )
        )

    @staticmethod
    def _comparison_table_row(item: ComparisonItemABC) -> typing.List[str]:

        entity = item.get_item()
        name = entity.name if isinstance(entity, SnapshotABC) else entity.subname

        if item.a is not None and item.b is not None:
            a, b = colorize("X", "green"), colorize("X", "green")
        elif item.a is None and item.b is not None:
            a, b = "", colorize("X", "blue")
        elif item.a is not None and item.b is None:
            a, b = colorize("X", "red"), ""

        return [
            "- " + colorize(name, "grey")
            if isinstance(entity, SnapshotABC)
            else colorize(name, "white"),
            a,
            b,
        ]

    @staticmethod
    def available(side: str, config: ConfigABC,) -> int:

        output, _ = Command.on_side(
            [
                "zfs",
                "get",
                "available",
                "-H",
                "-p",
                root(config[side]["zpool"], config[side]["prefix"]),
            ],
            side,
            config,
        ).run()

        return Property.from_params(*output.strip().split("\t")[1:]).value

    @classmethod
    def from_config(cls, side: str, config: ConfigABC,) -> ZpoolABC:

        root_dataset = root(config[side]["zpool"], config[side]["prefix"])

        output, errors, returncode, exception = Command.on_side(
            ["zfs", "get", "all", "-r", "-H", "-p", root_dataset,], side, config,
        ).run(returncode = True)

        if returncode != 0 and 'dataset does not exist' in errors:
            return cls(datasets=[], side=side, config=config,)
        if returncode != 0:
            raise exception

        output = [
            line.split("\t") for line in output.split("\n") if len(line.strip()) > 0
        ]
        entities = OrderedDict((line[0], []) for line in output)
        for line_list in output:
            entities[line_list[0]].append(line_list[1:])

        if not config.get("include_root", True):
            entities.pop(root_dataset)
            for name in [
                snapshot
                for snapshot in entities.keys()
                if snapshot.startswith(f"{root_dataset:s}@")
            ]:
                entities.pop(name)

        datasets = [
            Dataset.from_entities(
                name,
                OrderedDict(
                    (k, v)
                    for k, v in entities.items()
                    if k == name or k.startswith(f"{name:s}@")
                ),
                side,
                config,
            )
            for name in entities.keys()
            if "@" not in name
        ]
        datasets.sort(key=lambda dataset: dataset.name)

        return cls(datasets=datasets, side=side, config=config,)
