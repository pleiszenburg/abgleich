# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/core/filesystem.py: ZFS filesystem

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

from typing import Union

from typeguard import typechecked

from .abc import PropertyABC

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# TYPING
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

PropertyTypes = Union[str, int, float, None]

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@typechecked
class Property(PropertyABC):
    """
    Immutable.
    """

    def __init__(
        self,
        name: str,
        value: PropertyTypes,
        src: PropertyTypes = None,
    ):

        self._name = name
        self._value = value
        self._src = src

    @property
    def name(self) -> str:
        return self._name

    @property
    def value(self) -> PropertyTypes:
        return self._value

    @property
    def value_export(self) -> str:
        return self._export(self._value)

    @property
    def src(self) -> PropertyTypes:
        return self._src

    @property
    def src_export(self) -> str:
        return self._export(self._src)

    @classmethod
    def _import(cls, value: str) -> PropertyTypes:

        value = value.strip()

        if value.isnumeric():
            return int(value)

        if value.strip() == "" or value == "-" or value.lower() == "none":
            return None

        try:
            return float(value)
        except ValueError:
            pass

        return value

    def _export(self, value: PropertyTypes) -> str:

        return "-" if value is None else str(value)  # TODO improve!

    @classmethod
    def from_params(cls, name, value, src) -> PropertyABC:

        return cls(
            name=name,
            value=cls._import(value),
            src=cls._import(src),
        )
