# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/core/config.py: Handles configuration data

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
import yaml

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import FullLoader as Loader

from .abc import ConfigABC
from .lib import valid_name

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@typeguard.typechecked
class Config(ConfigABC, dict):
    @classmethod
    def from_fd(cls, fd: typing.TextIO):

        ssh_schema = {
            "compression": lambda v: isinstance(v, bool),
            "cipher": lambda v: isinstance(v, str) or v is None,
        }

        side_schema = {
            "zpool": lambda v: isinstance(v, str) and len(v) > 0,
            "prefix": lambda v: isinstance(v, str) or v is None,
            "host": lambda v: isinstance(v, str) and len(v) > 0,
            "user": lambda v: isinstance(v, str) or v is None,
        }

        root_schema = {
            "source": lambda v: cls._validate(data=v, schema=side_schema),
            "target": lambda v: cls._validate(data=v, schema=side_schema),
            "keep_snapshots": lambda v: isinstance(v, int) and v >= 1,
            "suffix": lambda v: v is None or (isinstance(v, str) and valid_name(v)),
            "digits": lambda v: isinstance(v, int) and v >= 1,
            "ignore": lambda v: isinstance(v, list)
            and all((isinstance(item, str) and len(item) > 0 for item in v)),
            "ssh": lambda v: cls._validate(data=v, schema=ssh_schema),
        }

        config = yaml.load(fd.read(), Loader=Loader)
        cls._validate(data=config, schema=root_schema)
        return cls(config)

    @classmethod
    def _validate(cls, data: typing.Dict, schema: typing.Dict):

        for field, validator in schema.items():
            if field not in data.keys():
                raise KeyError(f'missing configuration field "{field:s}"')
            if not validator(data[field]):
                raise ValueError(f'invalid value in field "{field:s}"')

        return True
