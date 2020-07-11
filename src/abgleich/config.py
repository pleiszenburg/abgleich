# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/config.py: Handles configuration data

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
from yaml import CLoader

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@typeguard.typechecked
class Config(dict):

    @classmethod
    def from_fd(cls, fd: typing.TextIO):

        config = yaml.load(fd.read(), Loader=CLoader)
        cls._validate(config)

        return cls(config)

    @classmethod
    def _validate(cls, config: typing.Dict):

        schema = {
            'host': lambda v: isinstance(v, str) and len(v) > 0,
            'local': cls._validate_location,
            'remote': cls._validate_location,
            'keep_snapshots': lambda v: isinstance(v, int) and v >= 1,
            'ignore': lambda v: isinstance(v, list) and all((isinstance(item, str) and len(item) > 0 for item in v)),
            }

        for field, validator in schema.items():
            if field not in config.keys():
                raise KeyError(f'missing configuration field "{field:s}"')
            if not validator(config[field]):
                raise ValueError(f'invalid value in field "{field:s}"')

    @classmethod
    def _validate_location(cls, location: typing.Dict):

        schema = {
            'zpool': lambda v: isinstance(v, str) and len(v) > 0,
            'prefix': lambda v: isinstance(v, str) or v is None,
            }

        for field, validator in schema.items():
            if field not in location.keys():
                return False
            if not validator(location[field]):
                return False

        return True
