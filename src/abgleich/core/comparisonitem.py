# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/core/comparisonitem.py: ZFS comparison item

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

from .abc import ComparisonItemABC, DatasetABC, SnapshotABC

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# TYPING
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

ComparisonGeneratorType = Union[
    Generator[DatasetABC, None, None],
    Generator[SnapshotABC, None, None],
    None,
]
ComparisonItemType = Union[
    DatasetABC,
    SnapshotABC,
    None,
]
ComparisonStrictItemType = Union[
    DatasetABC,
    SnapshotABC,
]

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@typechecked
class ComparisonItem(ComparisonItemABC):
    """
    Immutable.
    """

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

    @classmethod
    def list_from_singles(
        cls,
        items_a: ComparisonGeneratorType,
        items_b: ComparisonGeneratorType,
    ) -> List[ComparisonItemABC]:

        assert (items_a is not None) ^ (items_b is not None)

        if items_a is None:
            return [cls(None, item) for item in items_b]
        return [cls(item, None) for item in items_a]
