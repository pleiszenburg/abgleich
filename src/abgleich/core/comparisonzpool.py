# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/core/comparisonzpool.py: ZFS zpool comparison

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

from typing import Generator, List, Union

from typeguard import typechecked

from .abc import ComparisonItemABC, ComparisonZpoolABC, DatasetABC, ZpoolABC
from .comparisonitem import ComparisonItem

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@typechecked
class ComparisonZpool(ComparisonZpoolABC):
    """
    Immutable. No order, just name-based matching.
    """

    def __init__(
        self,
        a: Union[ZpoolABC, None],
        b: Union[ZpoolABC, None],
        merged: List[ComparisonItemABC],
    ):

        assert a is not None or b is not None
        if a is not None and b is not None:
            assert type(a) == type(b)

        self._a, self._b, self._merged = a, b, merged

    def __len__(self) -> int:

        return len(self._merged)

    @property
    def a(self) -> Union[ZpoolABC, None]:

        return self._a

    @property
    def b(self) -> Union[ZpoolABC, None]:

        return self._b

    @property
    def merged(self) -> Generator[ComparisonItemABC, None, None]:

        return (item for item in self._merged)

    @staticmethod
    def _merge_datasets(
        items_a: Generator[DatasetABC, None, None],
        items_b: Generator[DatasetABC, None, None],
    ) -> List[ComparisonItemABC]:

        items_a = {item.subname: item for item in items_a}
        items_b = {item.subname: item for item in items_b}

        names = list(items_a.keys() | items_b.keys())
        merged = [
            ComparisonItem(items_a.get(name, None), items_b.get(name, None))
            for name in names
        ]
        merged.sort(key=lambda item: item.get_item().name)

        return merged

    @classmethod
    def from_zpools(
        cls,
        zpool_a: Union[ZpoolABC, None],
        zpool_b: Union[ZpoolABC, None],
    ) -> ComparisonZpoolABC:

        assert zpool_a is not None or zpool_b is not None

        if (zpool_a is None) ^ (zpool_b is None):
            return cls(
                a=zpool_a,
                b=zpool_b,
                merged=ComparisonItem.list_from_singles(
                    getattr(zpool_a, "datasets", None),
                    getattr(zpool_b, "datasets", None),
                ),
            )

        assert zpool_a is not zpool_b
        assert zpool_a != zpool_b

        return cls(
            a=zpool_a,
            b=zpool_b,
            merged=cls._merge_datasets(zpool_a.datasets, zpool_b.datasets),
        )
