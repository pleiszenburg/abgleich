# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/zfs/zpool.py: ZFS zpool

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

from tabulate import tabulate
import typeguard

from .abc import ComparisonItemABC, DatasetABC, SnapshotABC, ZpoolABC
from .comparison import Comparison
from .dataset import Dataset
from .lib import join
from ..command import Command
from ..io import colorize, humanize_size

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@typeguard.typechecked
class Zpool(ZpoolABC):

    def __init__(
        self, datasets: typing.List[DatasetABC], side: str, config: typing.Dict,
    ):

        self._datasets = datasets
        self._side = side
        self._config = config

    def __eq__(self, other: ZpoolABC) -> bool:

        return self.side == other.side

    @property
    def datasets(self) -> typing.Generator[DatasetABC, None, None]:

        return (dataset for dataset in self._datasets)

    @property
    def side(self) -> str:

        return self._side

    def print_table(self):

        table = []
        for dataset in self._datasets:
            table.append(self._table_row(dataset))
            for snapshot in dataset.snapshots:
                table.append(self._table_row(snapshot))

        print(tabulate(
            table,
            headers=("NAME", "USED", "REFER", "compressratio"),
            tablefmt="github",
            colalign=("left", "right", "right", "decimal"),
            ))

    @staticmethod
    def _table_row(entity: typing.Union[SnapshotABC, DatasetABC]) -> typing.List[str]:

        return [
            '- ' + colorize(entity.name, "grey") if isinstance(entity, SnapshotABC) else colorize(entity.name, "white"),
            humanize_size(entity['used'].value, add_color=True),
            humanize_size(entity['referenced'].value, add_color=True),
            f'{entity["compressratio"].value:.02f}',
        ]

    def print_comparison_table(self, other: ZpoolABC):

        zpool_comparison = Comparison.from_zpools(self, other)
        table = []

        for dataset_item in zpool_comparison.merged:
            table.append(self._comparison_table_row(dataset_item))
            if dataset_item.complete:
                dataset_comparison = Comparison.from_datasets(dataset_item.a, dataset_item.b)
            elif dataset_item.a is not None:
                dataset_comparison = Comparison.from_datasets(dataset_item.a, None)
            else:
                dataset_comparison = Comparison.from_datasets(None, dataset_item.b)
            for snapshot_item in dataset_comparison.merged:
                table.append(self._comparison_table_row(snapshot_item))

        print(tabulate(
            table,
            headers=["NAME", self.side, other.side],
            tablefmt="github",
            ))

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
            '- ' + colorize(name, "grey") if isinstance(entity, SnapshotABC) else colorize(name, "white"),
            a,
            b,
        ]

    @classmethod
    def from_config(
        cls,
        side: str,
        config: typing.Dict,
        ) -> ZpoolABC:

        root = config[side]['zpool']
        if config[side]['prefix'] is not None:
            root = join(root, config[side]['prefix'])

        output, _ = Command.on_side(["zfs", "get", "all", "-r", "-H", "-p", root], side, config).run()
        output = [line.split('\t') for line in output.split('\n') if len(line.strip()) > 0]
        entities = {name: [] for name in {line[0] for line in output}}
        for line_list in output:
            entities[line_list[0]].append(line_list[1:])

        datasets = [
            Dataset.from_entities(
                name,
                {k: v for k, v in entities.items() if k == name or k.startswith(f'{name:s}@')},
                side,
                config,
                )
            for name in entities.keys()
            if '@' not in name
            ]
        datasets.sort(key = lambda dataset: dataset.name)

        return cls(
            datasets = datasets,
            side = side,
            config = config,
            )
