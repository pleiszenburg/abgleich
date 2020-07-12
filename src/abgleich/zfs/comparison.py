# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/zfs/comparison.py: ZFS comparison

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

from .abc import ComparisonABC, ComparisonItemABC, DatasetABC, SnapshotABC, ZpoolABC

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# TYPING
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

ComparisonParentTypes = typing.Union[
    ZpoolABC,
    DatasetABC,
    None,
    ]
ComparisonMergeTypes = typing.Union[
    typing.Generator[DatasetABC, None, None],
    typing.Generator[SnapshotABC, None, None],
    ]
ComparisonItemType = typing.Union[
    DatasetABC,
    SnapshotABC,
    None,
    ]
ComparisonStrictItemType = typing.Union[
    DatasetABC,
    SnapshotABC,
    ]

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@typeguard.typechecked
class Comparison(ComparisonABC):

    def __init__(
        self,
        a: ComparisonParentTypes,
        b: ComparisonParentTypes,
        merged: typing.List[ComparisonItemABC],
        ):

        assert type(a) == type(b)

        self._a, self._b, self._merged = a, b, merged

    @property
    def a(self) -> ComparisonParentTypes:

        return self._a

    @property
    def b(self) -> ComparisonParentTypes:

        return self._b

    @property
    def merged(self) -> typing.Generator[ComparisonItemABC, None, None]:

        return (item for item in self._merged)

    @staticmethod
    def _merge_items(
        items_a: ComparisonMergeTypes,
        items_b: ComparisonMergeTypes,
        ) -> typing.List[ComparisonItemABC]:

        items_a = {item.name: item for item in items_a}
        items_b = {item.name: item for item in items_b}

        names = list(items_a.keys() | items_b.keys())
        merged = [
            ComparisonItem(items_a.get(name, None), items_b.get(name, None))
            for name in names
            ]
        merged.sort(key = lambda item: item.get_item().sortkey)

        return merged

    @staticmethod
    def _single_items(
        items_a: typing.Union[ComparisonMergeTypes, None],
        items_b: typing.Union[ComparisonMergeTypes, None],
        ) -> typing.List[ComparisonItemABC]:

        assert items_a is not None or items_b is not None

        if items_a is None:
            return [ComparisonItem(None, item) for item in items_b]
        return [ComparisonItem(item, None) for item in items_a]

    @classmethod
    def from_zpools(
        cls,
        zpool_a: typing.Union[ZpoolABC, None],
        zpool_b: typing.Union[ZpoolABC, None],
        ) -> ComparisonABC:

        assert zpool_a is not None or zpool_b is not None

        if zpool_a is None or zpool_b is None:
            return cls(
                a = zpool_a,
                b = zpool_b,
                merged = cls._single_items(
                    getattr(zpool_a, 'datasets', None),
                    getattr(zpool_b, 'datasets', None),
                ),
            )

        assert zpool_a is not zpool_b
        assert zpool_a != zpool_b

        cls(
            a = zpool_a,
            b = zpool_b,
            merged = cls._merge_items(zpool_a.datasets, zpool_b.datasets),
        )

    @classmethod
    def from_datasets(
        cls,
        dataset_a: typing.Union[DatasetABC, None],
        dataset_b: typing.Union[DatasetABC, None],
        ) -> ComparisonABC:

        assert dataset_a is not None or dataset_b is not None

        if dataset_a is None or dataset_b is None:
            return cls(
                a = dataset_a,
                b = dataset_b,
                merged = cls._single_items(
                    getattr(dataset_a, 'snapshots', None),
                    getattr(dataset_b, 'snapshots', None),
                ),
            )

        assert dataset_a is not dataset_b
        assert dataset_a == dataset_b

        cls(
            a = dataset_a,
            b = dataset_b,
            merged = cls._merge_items(dataset_a.snapshots, dataset_b.snapshots),
        )


@typeguard.typechecked
class ComparisonItem(ComparisonItemABC):

    def __init__(self, a: ComparisonItemType, b: ComparisonItemType):

        assert a is not None or b is not None
        if a is not None and b is not None:
            assert type(a) == type(b)

        self._a, self._b = a, b

    def get_item(self) -> ComparisonStrictItemType:

        if self._a is not None:
            return self._a
        return self._b

    @property
    def complete(self) -> bool:

        return self._a is not None and self._b is not None

    @property
    def a(self) -> ComparisonItemType:

        return self._a

    @property
    def b(self) -> ComparisonItemType:

        return self._b
