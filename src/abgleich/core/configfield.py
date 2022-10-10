# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/core/configfield.py: Handles configuration fields

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

from typing import Callable, List, Union, Type

from .abc import ConfigFieldABC
from .debug import typechecked
from .i18n import t

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# TYPING
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

ConfigValueTypes = Union[List[str], str, int, float, bool, None]

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@typechecked
class ConfigField(ConfigFieldABC):
    """
    Mutable.
    """

    def __init__(
        self,
        name: str,
        description: str,
        type_: Type,
        validate: Callable = lambda v: True,
        default: ConfigValueTypes = None,
    ):

        self._name = name
        self._description = description
        self._type = type_
        self._default = default
        self._validate_func = validate

        if self._default is not None:
            if not self._validate(self._default):
                raise ValueError(f"invalid default value for {self._name}")

        self._value = None

    def __repr__(self) -> str:

        return (
            "<ConfigField "
            f'set="{"yes" if self.set else "no"}" '
            f'required="{str(self.required):s}" '
            f'type="{getattr(self._type, "__name__", str(type)):s}" '
            f'value="{str(self._value):s}" '
            f'default="{str(self._default):s}"'
            ">"
        )

    def copy(self) -> ConfigFieldABC:

        return type(self)(
            name=self._name,
            description=self._description,
            default=self._default,
            validate=self._validate_func,
            type_=self._type,
        )

    def prompt(self):

        default = ""
        if self._default is not None:
            default = f' [{self._default}]'
        msg = t('Enter a valid value for') + f' "{self._name:s}"{default:s}. {self.description:s}'
        print(msg)

        while True:
            value = input('? ')
            if len(value) == 0:
                value = self._default
            else:
                try:
                    value = self._type(value)
                except ValueError:
                    print(t('Can not be converted to type') + f' "{getattr(self._type, "__name__", str(type)):s}". ' + t('Try again.'))
                    continue
            try:
                self.value = value
                break
            except ValueError:
                print(t('Not a valid value for') + f' "{self.name:s}". ' + t('Try again.'))

    def _validate(self, value):

        return isinstance(value, self._type) and self._validate_func(value)

    @property
    def name(self) -> str:

        return self._name

    @property
    def description(self) -> str:

        return self._description

    @property
    def value(self) -> ConfigValueTypes:

        if self._value is not None:
            return self._value

        if self._default is None:
            raise ValueError(f"required value for {self._name} missing")

        return self._default

    @value.setter
    def value(self, value: ConfigValueTypes):

        if self._value is not None:
            raise ValueError(f"value for {self._name} has already been set")
        if value is None:
            return
        if not self._validate(value):
            raise ValueError(f"invalid value for {self._name}")

        self._value = value

    @property
    def valid(self) -> bool:

        if self._value is not None:
            return self._validate(self._value)

        # if self._default is not None
        return self._validate(self._default)

    @property
    def required(self) -> bool:

        return self._default is None

    @property
    def set(self) -> bool:

        return self._value is not None
