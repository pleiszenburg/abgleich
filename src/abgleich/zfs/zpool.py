# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/zfs/zpool.py: ZFS zpool

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

from .abc import FilesystemABC, ZpoolABC
from .filesystem import Filesystem
from ..command import Command

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@typeguard.typechecked
class Zpool(ZpoolABC):

    def __init__(
        self, filesystems: typing.List[FilesystemABC], side: str, config: typing.Dict,
    ):

        self._filesystems = filesystems
        self._side = side
        self._config = config

    @classmethod
    def from_config(cls, side: str, config: typing.Dict) -> ZpoolABC:

        status, out, err = Command.on_side(["zfs", "list", "-H", "-p"], side, config).run()

        return cls(
            filesystems = [
                Filesystem.from_line(line, side, config)
                for line in out.split('\n')
                if len(line.strip()) > 0
                ],
            side = side,
            config = config,
            )
