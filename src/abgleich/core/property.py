# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/core/filesystem.py: ZFS filesystem

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

from .abc import PropertyABC

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# TYPING
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

PropertyTypes = typing.Union[str, int, float, None]

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@typeguard.typechecked
class Property(PropertyABC):
    def __init__(
        self, name: str, value: PropertyTypes, src: PropertyTypes,
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
    def src(self) -> PropertyTypes:
        return self._src

    @classmethod
    def _convert(cls, value: str) -> PropertyTypes:

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

    @classmethod
    def from_params(cls, name, value, src) -> PropertyABC:

        return cls(name=name, value=cls._convert(value), src=cls._convert(src),)
