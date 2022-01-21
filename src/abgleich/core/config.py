# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/core/config.py: Handles configuration data

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

from typing import Dict, TextIO, Union

from typeguard import typechecked
import yaml

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import FullLoader as Loader

from .abc import ConfigABC, ConfigFieldABC
from .configspec import CONFIGSPEC

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@typechecked
class Config(ConfigABC):
    """
    Immutable.
    """

    def __init__(self, root: Union[str, None] = None, **kwargs: ConfigFieldABC):

        self._root = root
        self._fields = kwargs

    def __repr__(self):

        return "<Config>" if self._root is None else f'<Config root="{self._root:s}">'

    def __getitem__(self, key: str) -> ConfigFieldABC:

        return (
            self._fields[key]
            if self._root is None
            else self._fields[f"{self._root:s}/{key:s}"]
        )

    def group(self, root: str) -> ConfigABC:

        return type(self)(root=root, **self._fields)

    @classmethod
    def _flatten_dict_tree(cls, data: Dict, root: Union[str, None] = None) -> Dict:

        flat_data = {}

        for key, value in data.items():
            if not isinstance(key, str):
                raise TypeError("configuration key is no string", key)
            if root is not None:
                if len(root) > 0:
                    key = f"{root:s}/{key:s}"
            if isinstance(value, dict):
                flat_data.update(cls._flatten_dict_tree(data=value, root=key))
            else:
                flat_data[key] = value

        return flat_data

    @classmethod
    def from_fd(cls, fd: TextIO) -> ConfigABC:

        return cls.from_text(fd.read())

    @classmethod
    def from_text(cls, text: str) -> ConfigABC:

        config = yaml.load(text, Loader=Loader)

        if not isinstance(config, dict):
            raise TypeError("config is no dict", config)

        config_fields = {field.name: field.copy() for field in CONFIGSPEC}
        for key, value in cls._flatten_dict_tree(data=config).items():
            if key not in config_fields.keys():
                raise ValueError("unknown configuration key", key)
            config_fields[key].value = value

        if any((not field.valid for field in config_fields.values())):
            raise ValueError("configuration is not valid")

        return cls(**config_fields)
