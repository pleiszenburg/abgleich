# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/core/configspec.py: Defines configuration fields

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

from .configfield import ConfigField
from .lib import valid_name

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# SPEC
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

CONFIGSPEC = [
    ConfigField(
        name="keep_snapshots",
        validate=lambda v: isinstance(v, int) and v >= 1,
        default=1,
    ),
    ConfigField(
        name="keep_backlog",
        validate=lambda v: (isinstance(v, int) and v >= 0) or isinstance(v, bool),
        default=True,
    ),
    ConfigField(
        name="suffix",
        validate=lambda v: isinstance(v, str) and valid_name(v, min_len=0),
        default="",
    ),
    ConfigField(
        name="digits",
        validate=lambda v: isinstance(v, int) and v >= 1,
        default=2,
    ),
    ConfigField(
        name="always_changed",
        validate=lambda v: isinstance(v, bool),
        default=False,
    ),
    ConfigField(
        name="written_threshold",
        validate=lambda v: isinstance(v, int) and v > 0,
        default=1024 ** 2,
    ),
    ConfigField(
        name="check_diff",
        validate=lambda v: isinstance(v, bool),
        default=True,
    ),
    ConfigField(
        name="ignore",
        validate=lambda v: isinstance(v, list)
        and all((isinstance(item, str) and len(item) > 0 for item in v)),
        default=list(),
    ),
    ConfigField(
        name="include_root",
        validate=lambda v: isinstance(v, bool),
        default=True,
    ),
    ConfigField(
        name="compatibility/tagging",
        validate=lambda v: isinstance(v, bool),
        default=False,
    ),
    ConfigField(
        name="compatibility/target_samba_noshare",
        validate=lambda v: isinstance(v, bool),
        default=False,
    ),
    ConfigField(
        name="compatibility/target_autosnapshot_ignore",
        validate=lambda v: isinstance(v, bool),
        default=False,
    ),
    ConfigField(
        name="ssh/compression",
        validate=lambda v: isinstance(v, bool),
        default=False,
    ),
    ConfigField(
        name="ssh/cipher",
        validate=lambda v: isinstance(v, str),
        default="",
    ),
]

for _side in ("source", "target"):

    CONFIGSPEC.extend(
        [
            ConfigField(
                name=f"{_side}/zpool",
                validate=lambda v: isinstance(v, str) and len(v) > 0,
            ),
            ConfigField(
                name=f"{_side}/prefix",
                validate=lambda v: isinstance(v, str),
                default="",
            ),
            ConfigField(
                name=f"{_side}/host",
                validate=lambda v: isinstance(v, str) and len(v) > 0,
                default="localhost",
            ),
            ConfigField(
                name=f"{_side}/user",
                validate=lambda v: isinstance(v, str),
                default="",
            ),
            ConfigField(
                name=f"{_side}/port",
                validate=lambda v: isinstance(v, int) and v >= 0,
                default=0,
            ),
            ConfigField(
                name=f"{_side}/processing",
                validate=lambda v: isinstance(v, str),
                default="",
            ),
        ]
    )

del _side
