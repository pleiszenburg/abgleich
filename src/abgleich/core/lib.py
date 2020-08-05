# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/core/lib.py: ZFS library

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

import re
import typing

import typeguard

from .abc import ConfigABC
from .command import Command

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ROUTINES
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@typeguard.typechecked
def is_host_up(side: str, config: ConfigABC) -> bool:

    assert side in ("source", "target")
    if config[side]["host"] == "localhost":
        return True

    _, _, returncode, _ = Command.on_side(["exit"], side, config).run(returncode=True)
    assert returncode in (0, 255)
    return returncode == 0


@typeguard.typechecked
def join(*args: str) -> str:

    if len(args) < 2:
        raise ValueError("not enough elements to join")

    args = [arg.strip("/ \t\n") for arg in args]

    if any((len(arg) == 0 for arg in args)):
        raise ValueError("can not join empty path elements")

    return "/".join(args)


@typeguard.typechecked
def root(zpool: str, prefix: typing.Union[str, None]) -> str:

    if prefix is None:
        return zpool
    return join(zpool, prefix)


_name_re = re.compile("^[A-Za-z0-9_]+$")


@typeguard.typechecked
def valid_name(name: str, min_len: int = 1) -> bool:

    assert min_len >= 0

    if len(name) < min_len:
        return False
    return bool(_name_re.match(name))
