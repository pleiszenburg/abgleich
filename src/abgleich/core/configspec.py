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
from .i18n import t
from .lib import valid_name

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# SPEC
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

CONFIGSPEC = [
    ConfigField(
        name="keep_snapshots",
        description=t(
            f"Defines how many snapshots should always be kept on the source side. Minimum is one."
        ),
        validate=lambda v: isinstance(v, int) and v >= 1,
        default=1,
    ),
    ConfigField(
        name="keep_backlog",
        description=t(
            f"Degines how many snapshots should always be kept on the target side beyond the required overlap with the source side. Set to -1 for all."
        ),
        validate=lambda v: isinstance(v, int) and (v >= -1),
        default=-1,
    ),
    ConfigField(
        name="suffix",
        description=t(f"The suffix that snapshot names should carry."),
        validate=lambda v: isinstance(v, str) and valid_name(v, min_len=0),
        default="",
    ),
    ConfigField(
        name="digits",
        description=t(
            f"Snapshots made on the same day get enumerated within their name. Defines how many digits this number should have."
        ),
        validate=lambda v: isinstance(v, int) and v >= 1,
        default=2,
    ),
    ConfigField(
        name="always_changed",
        description=t(
            f"Assume that datasets and volumes have always been changed, forcing `abgleich snap` to create snapshots for all of them on every run."
        ),
        validate=lambda v: isinstance(v, bool),
        default=False,
    ),
    ConfigField(
        name="written_threshold",
        description=t(
            f"The creation of a snapshot is triggered if at least this many bytes have been written to a dataset or volume."
        ),
        validate=lambda v: isinstance(v, int) and v > 0,
        default=1024**2,
    ),
    ConfigField(
        name="check_diff",
        description=t(
            f"Check the `diff` of a dataset if more than zero but less than `written_threshold` bytes have been written to it before creating a snapshot. Generating `diff`s can be slow or even fail under certain circumstances."
        ),
        validate=lambda v: isinstance(v, bool),
        default=True,
    ),
    ConfigField(
        name="ignore",
        description=t(
            f"Ignore the following list of datasets and volumes for all operations."
        ),
        validate=lambda v: isinstance(v, list)
        and all((isinstance(item, str) and len(item) > 0 for item in v)),
        default=list(),
    ),
    ConfigField(
        name="include_root",
        description=t(
            f"Include the root (source prefix & target prefix) into all operations."
        ),
        validate=lambda v: isinstance(v, bool),
        default=True,
    ),
    ConfigField(
        name="compatibility/tagging",
        description=t(
            f"Make `abgleich` work around snapshots created by other tools on the source side."
        ),
        validate=lambda v: isinstance(v, bool),
        default=False,
    ),
    ConfigField(
        name="compatibility/target_samba_noshare",
        description=t(
            f"Tell ZFS on the target side to not expose datasets and volumes via NFS."
        ),
        validate=lambda v: isinstance(v, bool),
        default=False,
    ),
    ConfigField(
        name="compatibility/target_autosnapshot_ignore",
        description=t(
            f"Tell `zfs-auto-snapshot` on the target side to ignore datasets and volumes."
        ),
        validate=lambda v: isinstance(v, bool),
        default=False,
    ),
    ConfigField(
        name="ssh/compression",
        description=t(f"Activate compression during `ssh` transfers."),
        validate=lambda v: isinstance(v, bool),
        default=False,
    ),
    ConfigField(
        name="ssh/cipher",
        description=t(f"Specify `OpenSSH` cipher."),
        validate=lambda v: isinstance(v, str),
        default="",
    ),
]

for _side in ("source", "target"):

    CONFIGSPEC.extend(
        [
            ConfigField(
                name=f"{_side}/zpool",
                description=t(f"Name of zpool on {_side:s} side."),
                validate=lambda v: isinstance(v, str) and len(v) > 0,
            ),
            ConfigField(
                name=f"{_side}/prefix",
                description=t(f"Path to root dataset/volume in zpool on {_side:s} side."),
                validate=lambda v: isinstance(v, str),
                default="",
            ),
            ConfigField(
                name=f"{_side}/host",
                description=t(f"Hostname or IP address of {_side:s} side."),
                validate=lambda v: isinstance(v, str) and len(v) > 0,
                default="localhost",
            ),
            ConfigField(
                name=f"{_side}/user",
                description=t(f"Username on {_side:s} side (SSH)."),
                validate=lambda v: isinstance(v, str),
                default="",
            ),
            ConfigField(
                name=f"{_side}/port",
                description=t(f"Port on {_side:s} side (SSH)."),
                validate=lambda v: isinstance(v, int) and v >= 0,
                default=0,
            ),
            ConfigField(
                name=f"{_side}/processing",
                description=t(
                    "Pre-processing command on source side." if _side == 'source' else "Post-processing command on target side."
                ),
                validate=lambda v: isinstance(v, str),
                default="",
            ),
        ]
    )

del _side
