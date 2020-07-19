# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/core/comparison.py: ZFS comparison

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

import itertools
import typing

import typeguard

from .abc import ComparisonABC, ComparisonItemABC, DatasetABC, SnapshotABC, ZpoolABC

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# TYPING
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

ComparisonParentTypes = typing.Union[
    ZpoolABC, DatasetABC, None,
]
ComparisonMergeTypes = typing.Union[
    typing.Generator[DatasetABC, None, None], typing.Generator[SnapshotABC, None, None],
]
ComparisonItemType = typing.Union[
    DatasetABC, SnapshotABC, None,
]
ComparisonStrictItemType = typing.Union[
    DatasetABC, SnapshotABC,
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

        assert a is not None or b is not None
        if a is not None and b is not None:
            assert type(a) == type(b)

        self._a, self._b, self._merged = a, b, merged

    def __len__(self) -> int:

        return len(self._merged)

    @property
    def a(self) -> ComparisonParentTypes:

        return self._a

    @property
    def a_head(self) -> typing.List[ComparisonStrictItemType]:

        return self._head(
            source=[item.a for item in self._merged],
            target=[item.b for item in self._merged],
        )

    @property
    def a_overlap_tail(self) -> typing.List[ComparisonStrictItemType]:

        return self._overlap_tail(
            source=[item.a for item in self._merged],
            target=[item.b for item in self._merged],
        )

    @property
    def b(self) -> ComparisonParentTypes:

        return self._b

    @property
    def b_head(self) -> typing.List[ComparisonStrictItemType]:

        return self._head(
            source=[item.b for item in self._merged],
            target=[item.a for item in self._merged],
        )

    @property
    def b_overlap_tail(self) -> typing.List[ComparisonStrictItemType]:

        return self._overlap_tail(
            source=[item.b for item in self._merged],
            target=[item.a for item in self._merged],
        )

    @property
    def merged(self) -> typing.Generator[ComparisonItemABC, None, None]:

        return (item for item in self._merged)

    @classmethod
    def _head(
        cls,
        source: typing.List[ComparisonItemType],
        target: typing.List[ComparisonItemType],
    ) -> typing.List[ComparisonItemType]:
        """
        Returns new elements from source.
        If target is empty, returns source.
        If head of target and head of source are identical, returns empty list.
        """

        source, target = cls._strip_none(source), cls._strip_none(target)

        if any((element is None for element in source)):
            raise ValueError("source is not consecutive")
        if any((element is None for element in target)):
            raise ValueError("target is not consecutive")

        if len(source) == 0:
            raise ValueError("source must not be empty")

        if len(set([item.name for item in source])) != len(source):
            raise ValueError("source contains doublicate entires")
        if len(set([item.name for item in target])) != len(target):
            raise ValueError("target contains doublicate entires")

        if len(target) == 0:
            return source  # all of source, target is empty

        try:
            source_index = [item.name for item in source].index(target[-1].name)
        except ValueError:
            raise ValueError("last target element not in source")

        old_source = source[: source_index + 1]

        if len(old_source) <= len(target):
            if target[-len(old_source) :] != old_source:
                raise ValueError(
                    "no clean match between end of target and beginning of source"
                )
        else:
            if target != source[source_index + 1 - len(target) : source_index + 1]:
                raise ValueError(
                    "no clean match between entire target and beginning of source"
                )

        return source[source_index + 1 :]

    @classmethod
    def _overlap_tail(
        cls,
        source: typing.List[ComparisonItemType],
        target: typing.List[ComparisonItemType],
    ) -> typing.List[ComparisonItemType]:
        """
        Overlap must include first element of source.
        """

        source, target = cls._strip_none(source), cls._strip_none(target)

        if len(source) == 0 or len(target) == 0:
            return []

        if any((element is None for element in source)):
            raise ValueError("source is not consecutive")
        if any((element is None for element in target)):
            raise ValueError("target is not consecutive")

        source_names = {item.name for item in source}
        target_names = {item.name for item in target}

        if len(source_names) != len(source):
            raise ValueError("source contains doublicate entires")
        if len(target_names) != len(target):
            raise ValueError("target contains doublicate entires")

        overlap_tail = []
        for item in source:
            if item.name not in target_names:
                break
            overlap_tail.append(item)

        if len(overlap_tail) == 0:
            return overlap_tail

        target_index = target.index(overlap_tail[0])
        if overlap_tail != target[target_index : target_index + len(overlap_tail)]:
            raise ValueError("no clean match in overlap area")

        return overlap_tail

    @classmethod
    def _strip_none(
        cls, elements: typing.List[ComparisonItemType]
    ) -> typing.List[ComparisonItemType]:

        elements = cls._left_strip_none(elements)  # left strip
        elements.reverse()  # flip into reverse
        elements = cls._left_strip_none(elements)  # right strip
        elements.reverse()  # flip back

        return elements

    @staticmethod
    def _left_strip_none(
        elements: typing.List[ComparisonItemType],
    ) -> typing.List[ComparisonItemType]:

        return list(itertools.dropwhile(lambda element: element is None, elements))

    @staticmethod
    def _single_items(
        items_a: typing.Union[ComparisonMergeTypes, None],
        items_b: typing.Union[ComparisonMergeTypes, None],
    ) -> typing.List[ComparisonItemABC]:

        assert items_a is not None or items_b is not None

        if items_a is None:
            return [ComparisonItem(None, item) for item in items_b]
        return [ComparisonItem(item, None) for item in items_a]

    @staticmethod
    def _merge_datasets(
        items_a: typing.Generator[DatasetABC, None, None],
        items_b: typing.Generator[DatasetABC, None, None],
    ) -> typing.List[ComparisonItemABC]:

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
        zpool_a: typing.Union[ZpoolABC, None],
        zpool_b: typing.Union[ZpoolABC, None],
    ) -> ComparisonABC:

        assert zpool_a is not None or zpool_b is not None

        if zpool_a is None or zpool_b is None:
            return cls(
                a=zpool_a,
                b=zpool_b,
                merged=cls._single_items(
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

    @staticmethod
    def _merge_snapshots(
        items_a: typing.Generator[SnapshotABC, None, None],
        items_b: typing.Generator[SnapshotABC, None, None],
    ) -> typing.List[ComparisonItemABC]:

        items_a = list(items_a)
        items_b = list(items_b)
        names_a = [item.name for item in items_a]
        names_b = [item.name for item in items_b]

        assert len(set(names_a)) == len(items_a)  # unique names
        assert len(set(names_b)) == len(items_b)  # unique names

        if len(items_a) == 0 and len(items_b) == 0:
            return []
        if len(items_a) == 0:
            return [ComparisonItem(None, item) for item in items_b]
        if len(items_b) == 0:
            return [ComparisonItem(item, None) for item in items_a]

        try:
            start_b = names_a.index(names_b[0])
        except ValueError:
            start_b = None
        try:
            start_a = names_b.index(names_a[0])
        except ValueError:
            start_a = None

        assert start_a is not None or start_b is not None  # overlap

        prefix_a = [] if start_a is None else [None for _ in range(start_a)]
        prefix_b = [] if start_b is None else [None for _ in range(start_b)]
        items_a = prefix_a + items_a
        items_b = prefix_b + items_b
        suffix_a = (
            []
            if len(items_a) >= len(items_b)
            else [None for _ in range(len(items_b) - len(items_a))]
        )
        suffix_b = (
            []
            if len(items_b) >= len(items_a)
            else [None for _ in range(len(items_a) - len(items_b))]
        )
        items_a = items_a + suffix_a
        items_b = items_b + suffix_b

        assert len(items_a) == len(items_b)

        alt_a, alt_b, state_a, state_b = 0, 0, False, False
        merged = []
        for item_a, item_b in zip(items_a, items_b):
            new_state_a, new_state_b = item_a is not None, item_b is not None
            if new_state_a != state_a:
                alt_a, state_a = alt_a + 1, new_state_a
                if alt_a > 2:
                    raise ValueError("gap in snapshot series")
            if new_state_b != state_b:
                alt_b, state_b = alt_b + 1, new_state_b
                if alt_b > 2:
                    raise ValueError("gap in snapshot series")
            if state_a and state_b:
                if item_a.name != item_b.name:
                    raise ValueError("inconsistent snapshot names")
            merged.append(ComparisonItem(item_a, item_b))

        return merged

    @classmethod
    def from_datasets(
        cls,
        dataset_a: typing.Union[DatasetABC, None],
        dataset_b: typing.Union[DatasetABC, None],
    ) -> ComparisonABC:

        assert dataset_a is not None or dataset_b is not None

        if dataset_a is None or dataset_b is None:
            return cls(
                a=dataset_a,
                b=dataset_b,
                merged=cls._single_items(
                    getattr(dataset_a, "snapshots", None),
                    getattr(dataset_b, "snapshots", None),
                ),
            )

        assert dataset_a is not dataset_b
        assert dataset_a == dataset_b

        return cls(
            a=dataset_a,
            b=dataset_b,
            merged=cls._merge_snapshots(dataset_a.snapshots, dataset_b.snapshots),
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
