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

import yaml

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import FullLoader as Loader

try:
    from yaml import CDumper as Dumper
except ImportError:
    from yaml import Dumper

from .abc import ConfigABC, ConfigFieldABC
from .configspec import CONFIGSPEC
from .debug import typechecked

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
        """
        Easy access to configuration groups (aka paths)
        """

        return type(self)(root=root, **self._fields)

    def to_fd(self, fd: TextIO):
        """
        Export configuration to handle on opened YAML file
        """

        fd.write(self.to_text())

    def to_text(self):
        """
        Export configuration to YAML string
        """

        config = {
            name: field.value for name, field in self._fields.items() if field.set
        }

        config = self._flat_to_tree(config)

        return yaml.dump(config, Dumper=Dumper, allow_unicode=True, indent=4)

    @classmethod
    def _tree_to_flat(cls, data: Dict, root: Union[str, None] = None) -> Dict:

        flat = {}

        for key, value in data.items():
            if not isinstance(key, str):
                raise TypeError("configuration key is no string", key)
            if root is not None:
                if len(root) > 0:
                    key = f"{root:s}/{key:s}"
            if isinstance(value, dict):
                flat.update(cls._tree_to_flat(data=value, root=key))
            else:
                flat[key] = value

        return flat

    @classmethod
    def _flat_to_tree(cls, data: Dict) -> Dict:

        tree = {}

        for key, value in data.items():

            if "/" not in key:
                tree[key] = value
                continue

            root, key = key.split("/", 1)
            if root not in tree.keys():
                tree[root] = {}
            tree[root][key] = value

        for key, value in tree.items():
            if not isinstance(value, dict):
                continue
            tree[key] = cls._flat_to_tree(value)

        return tree

    @classmethod
    def from_fd(cls, fd: TextIO) -> ConfigABC:
        """
        Import configuration from handle on opened YAML file
        """

        return cls.from_text(fd.read())

    @classmethod
    def from_text(cls, text: str) -> ConfigABC:
        """
        Import configuration from YAML string
        """

        raw = yaml.load(text, Loader=Loader)

        if not isinstance(raw, dict):
            raise TypeError("raw configuration is no dict", raw)

        config = {field.name: field.copy() for field in CONFIGSPEC}
        for key, value in cls._tree_to_flat(data=raw).items():
            if key not in config.keys():
                raise ValueError("unknown configuration key", key)
            config[key].value = value

        if any((not field.valid for field in config.values())):
            raise ValueError("configuration is not valid")

        return cls(**config)

    @classmethod
    def from_cli(cls):

        config = {field.name: field.copy() for field in CONFIGSPEC}

        source_keys = [key for key in config.keys() if key.startswith('source/')]
        target_keys = [key for key in config.keys() if key.startswith('target/')]
        other_keys = [key for key in config.keys() if key not in source_keys and key not in target_keys]

        source_keys.sort()
        target_keys.sort()
        other_keys.sort()

        for keys in (source_keys, target_keys, other_keys):
            for key in keys:
                config[key].prompt()

        return cls(**config)
