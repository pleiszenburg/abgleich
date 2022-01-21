# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/core/zpool.py: ZFS zpool

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

from collections import OrderedDict
from typing import Generator, List, Tuple, Union

from tabulate import tabulate
from typeguard import typechecked

from .abc import (
    ComparisonItemABC,
    ConfigABC,
    DatasetABC,
    SnapshotABC,
    TransactionListABC,
    ZpoolABC,
)
from .command import Command
from .comparisondataset import ComparisonDataset
from .comparisonzpool import ComparisonZpool
from .dataset import Dataset
from .i18n import t
from .io import colorize, humanize_size
from .lib import join, root
from .property import Property
from .transaction import Transaction
from .transactionlist import TransactionList

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@typechecked
class Zpool(ZpoolABC):
    """
    Immutable.
    """

    def __init__(
        self,
        datasets: List[DatasetABC],
        side: str,
        config: ConfigABC,
    ):

        self._datasets = datasets
        self._side = side
        self._config = config

        self._root = root(
            config[f"{side:s}/zpool"].value, config[f"{side:s}/prefix"].value
        )

    def __eq__(self, other: ZpoolABC) -> bool:

        return self.side == other.side

    @property
    def datasets(self) -> Generator[DatasetABC, None, None]:

        return (dataset for dataset in self._datasets)

    @property
    def side(self) -> str:

        return self._side

    @property
    def root(self) -> str:

        return self._root

    def get_cleanup_transactions(
        self,
        other: ZpoolABC,
    ) -> TransactionListABC:

        assert self.side != other.side
        assert self.side in ("source", "target")
        assert other.side in ("source", "target")

        zpool_comparison = ComparisonZpool.from_zpools(self, other)
        transactions = TransactionList()

        for dataset_item in zpool_comparison.merged:
            transactions.extend(self._get_cleanup_from_datasetitem(dataset_item))

        return transactions

    def generate_cleanup_transactions(
        self,
        other: ZpoolABC,
    ) -> Generator[Tuple[int, Union[None, TransactionListABC]], None, None]:

        assert self.side != other.side
        assert self.side in ("source", "target")
        assert other.side in ("source", "target")

        zpool_comparison = ComparisonZpool.from_zpools(self, other)

        yield len(zpool_comparison), None

        for index, dataset_item in enumerate(zpool_comparison.merged):
            yield index, self._get_cleanup_from_datasetitem(dataset_item)

    def _get_cleanup_from_datasetitem(
        self,
        dataset_item: ComparisonItemABC,
    ) -> TransactionListABC:

        if dataset_item.get_item().ignore:
            return TransactionList()
        if dataset_item.a is None or dataset_item.b is None:
            return TransactionList()
        if self.side == "target" and self._config["keep_backlog"].value == True:
            return TransactionList()

        dataset_comparison = ComparisonDataset.from_datasets(
            dataset_item.a, dataset_item.b, self._config
        )  # TODO namespace

        if self.side == "source":
            snapshots = dataset_comparison.a_overlap_tail[
                : -self._config["keep_snapshots"].value
            ]
        else:  # target
            if self._config["keep_backlog"].value in (False, 0):
                keep_backlog = None
            else:
                keep_backlog = -self._config["keep_backlog"].value
            snapshots = dataset_comparison.a_disjoint_tail[:keep_backlog]

        transactions = TransactionList()

        for snapshot in snapshots:
            transactions.extend(snapshot.get_cleanup_transactions())

        return transactions

    def get_backup_transactions(
        self,
        other: ZpoolABC,
    ) -> TransactionListABC:

        assert self.side == "source"
        assert other.side == "target"

        zpool_comparison = ComparisonZpool.from_zpools(self, other)
        transactions = TransactionList()

        for dataset_item in zpool_comparison.merged:
            transactions.extend(
                self._get_backup_transactions_from_datasetitem(other, dataset_item)
            )

        transactions.extend(self._get_backup_propery_transactions(other))

        return transactions

    def generate_backup_transactions(
        self,
        other: ZpoolABC,
    ) -> Generator[Tuple[int, Union[None, TransactionListABC]], None, None]:

        assert self.side == "source"
        assert other.side == "target"

        zpool_comparison = ComparisonZpool.from_zpools(self, other)

        yield len(zpool_comparison), None

        for index, dataset_item in enumerate(zpool_comparison.merged):
            yield index, self._get_backup_transactions_from_datasetitem(
                other, dataset_item
            )

        for transaction in self._get_backup_propery_transactions(other):
            yield len(zpool_comparison) - 1, transaction

    def _get_backup_transactions_from_datasetitem(
        self,
        other: ZpoolABC,
        dataset_item: ComparisonItemABC,
    ) -> TransactionListABC:

        if dataset_item.get_item().ignore:
            return TransactionList()
        if dataset_item.a is None:
            return TransactionList()

        if dataset_item.b is None:
            snapshots = list(dataset_item.a.snapshots)
        else:
            dataset_comparison = ComparisonDataset.from_datasets(
                dataset_item.a, dataset_item.b, self._config
            )  # TODO namespace
            snapshots = dataset_comparison.a_disjoint_head

        if len(snapshots) == 0:
            return TransactionList()

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

        transactions = TransactionList()

        for snapshot in snapshots:
            transactions.extend(
                snapshot.get_backup_transactions(
                    source_dataset,
                    target_dataset,
                )
            )

        return transactions

    def _get_backup_propery_transactions(self, other: ZpoolABC) -> TransactionListABC:

        transactions = TransactionList()

        if self._config["compatibility/target_samba_noshare"].value:
            transactions.append(
                Transaction.set_property(
                    item=other.root,
                    property=Property(name="sharesmb", value="off"),
                    side="target",
                    config=self._config,
                )
            )

        if self._config["compatibility/target_autosnapshot_ignore"].value:
            transactions.append(
                Transaction.set_property(
                    item=other.root,
                    property=Property(name="com.sun:auto-snapshot", value="false"),
                    side="target",
                    config=self._config,
                )
            )

        return transactions

    def get_snapshot_transactions(self) -> TransactionListABC:

        assert self._side == "source"

        transactions = TransactionList()

        for dataset in self._datasets:
            transactions.extend(self._get_snapshot_transactions_from_dataset(dataset))

        return transactions

    def generate_snapshot_transactions(
        self,
    ) -> Generator[Tuple[int, Union[None, TransactionListABC]], None, None]:

        assert self._side == "source"

        yield len(self._datasets), None

        for index, dataset in enumerate(self._datasets):
            yield index, self._get_snapshot_transactions_from_dataset(dataset)

    def _get_snapshot_transactions_from_dataset(
        self, dataset: DatasetABC
    ) -> TransactionListABC:

        if dataset.ignore:
            return TransactionList()
        if (
            dataset.get("mountpoint").value is None
            and dataset["type"].value == "filesystem"
        ):
            return TransactionList()
        if not dataset.changed:  # TODO namespace
            return TransactionList()

        return dataset.get_snapshot_transactions()

    def print_table(self):

        table = []
        for dataset in self._datasets:
            table.append(self._table_row(dataset, ignore=dataset.ignore))
            for snapshot in dataset.snapshots:
                table.append(self._table_row(snapshot))

        if len(table) == 0:
            print("(empty)")
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
    def _table_row(
        entity: Union[SnapshotABC, DatasetABC], ignore: bool = False
    ) -> List[str]:

        color = "white" if not ignore else "red"

        return [
            "- " + colorize(entity.name, "grey")
            if isinstance(entity, SnapshotABC)
            else colorize(entity.name, color),
            humanize_size(entity["used"].value, add_color=True),
            humanize_size(entity["referenced"].value, add_color=True),
            f'{entity["compressratio"].value:.02f}',
        ]

    def print_comparison_table(self, other: ZpoolABC):

        zpool_comparison = ComparisonZpool.from_zpools(self, other)
        table = []

        for dataset_item in zpool_comparison.merged:
            table.append(
                self._comparison_table_row(
                    dataset_item, ignore=dataset_item.get_item().ignore
                )
            )
            if dataset_item.complete:
                dataset_comparison = ComparisonDataset.from_datasets(
                    dataset_item.a, dataset_item.b, self._config
                )
            elif dataset_item.a is not None:
                dataset_comparison = ComparisonDataset.from_datasets(
                    dataset_item.a, None, self._config
                )
            else:
                dataset_comparison = ComparisonDataset.from_datasets(
                    None, dataset_item.b, self._config
                )
            for snapshot_item in dataset_comparison.merged:
                table.append(
                    self._comparison_table_row(
                        snapshot_item, ignore=dataset_item.get_item().ignore
                    )
                )

        print(
            tabulate(
                table,
                headers=[t("NAME"), t(self.side), t(other.side)],
                tablefmt="github",
            )
        )

    @staticmethod
    def _comparison_table_row(
        item: ComparisonItemABC, ignore: bool = False
    ) -> List[str]:

        color1, color2 = ("white", "grey") if not ignore else ("red", "yellow")
        colorR, colorG, colorB = (
            ("red", "green", "blue") if not ignore else ("grey", "grey", "grey")
        )

        symbol = "X"

        entity = item.get_item()
        name = entity.name if isinstance(entity, SnapshotABC) else entity.subname

        if item.a is not None and item.b is not None:
            a, b = colorize(symbol, colorG), colorize(symbol, colorG)
        elif item.a is None and item.b is not None:
            a, b = "", colorize(symbol, colorB)
        elif item.a is not None and item.b is None:
            a, b = colorize(symbol, colorR), ""

        return [
            "- " + colorize(name, color2)
            if isinstance(entity, SnapshotABC)
            else colorize(name, color1),
            a,
            b,
        ]

    @staticmethod
    def available(
        side: str,
        config: ConfigABC,
    ) -> int:

        output, _ = (
            Command.from_list(
                [
                    "zfs",
                    "get",
                    "available",
                    "-H",
                    "-p",
                    root(
                        config[f"{side:s}/zpool"].value,
                        config[f"{side:s}/prefix"].value,
                    ),
                ]
            )
            .on_side(side=side, config=config)
            .run()
        )

        return Property.from_params(*output[0].strip().split("\t")[1:]).value

    @classmethod
    def from_config(
        cls,
        side: str,
        config: ConfigABC,
    ) -> ZpoolABC:

        root_dataset = root(
            config[f"{side:s}/zpool"].value, config[f"{side:s}/prefix"].value
        )

        output, errors, returncode, exception = (
            Command.from_list(
                [
                    "zfs",
                    "get",
                    "all",
                    "-r",
                    "-H",
                    "-p",
                    root_dataset,
                ]
            )
            .on_side(side=side, config=config)
            .run(returncode=True)
        )

        if returncode[0] != 0 and "dataset does not exist" in errors[0]:
            return cls(
                datasets=[],
                side=side,
                config=config,
            )
        if returncode[0] != 0:
            raise exception

        output = [
            line.split("\t") for line in output[0].split("\n") if len(line.strip()) > 0
        ]
        entities = OrderedDict((line[0], []) for line in output)
        for line_list in output:
            entities[line_list[0]].append(line_list[1:])

        if not config["include_root"].value:
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

        return cls(
            datasets=datasets,
            side=side,
            config=config,
        )
