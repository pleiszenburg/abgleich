# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/core/command.py: Sub-process wrapper for commands

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

from subprocess import Popen, PIPE
from typing import List, Tuple, Union
import shlex

from typeguard import typechecked

from .abc import CommandABC, ConfigABC

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@typechecked
class Command(CommandABC):
    """
    Immutable.
    """

    def __init__(self, cmd: List[List[str]]):

        self._cmd = [fragment.copy() for fragment in cmd]

    def __repr__(self) -> str:

        return "<Command>"

    def __str__(self) -> str:

        return " | ".join([shlex.join(fragment) for fragment in self._cmd])

    def __len__(self) -> int:

        return len(self._cmd)

    def __or__(self, other: CommandABC) -> CommandABC:  # pipe

        return type(self)(self.cmd + other.cmd)

    @staticmethod
    def _com_to_str(com: Union[str, bytes, None]) -> str:

        if com is None:
            return ""

        if isinstance(com, bytes):
            return com.decode("utf-8")

        return com

    def run(
        self, returncode: bool = False
    ) -> Union[
        Tuple[List[str], List[str], List[int], Exception], Tuple[List[str], List[str]]
    ]:

        procs = []  # all processes, connected with pipes

        for index, fragment in enumerate(self._cmd):  # create & connect processes

            stdin = None if index == 0 else procs[-1].stdout  # output of last process
            proc = Popen(fragment, stdout=PIPE, stderr=PIPE, stdin=stdin,)
            procs.append(proc)

        output, errors, status = [], [], []

        for proc in procs[::-1]:  # inverse order, last process first

            out, err = proc.communicate()
            output.append(self._com_to_str(out))
            errors.append(self._com_to_str(err))
            status.append(int(proc.returncode))

        output.reverse()
        errors.reverse()
        status.reverse()

        exception = SystemError("command failed", str(self), output, errors)

        if returncode:
            return output, errors, status, exception

        if any((code != 0 for code in status)):  # some fragment failed:
            raise exception

        return output, errors

    def on_side(self, side: str, config: ConfigABC) -> CommandABC:

        if config[f'{side:s}/host'] == "localhost":
            return self

        side_config = config.group(side)
        ssh_config = config.group("ssh")

        cmd_ssh = [
            "ssh",
            "-T",  # Disable pseudo-terminal allocation
            "-p",  # Port parameter
            f'{side_config["port"]:d}',
            "-o",  # Option parameter
            "Compression=yes" if ssh_config["compression"] else "Compression=no",
        ]
        if ssh_config["cipher"] is not None:
            cmd_ssh.extend(("-c", ssh_config["cipher"]))
        cmd_ssh.extend([f'{side_config["user"]:s}@{side_config["host"]:s}', str(self)])

        return type(self)([cmd_ssh])

    @property
    def cmd(self) -> List[List[str]]:

        return [fragment.copy() for fragment in self._cmd]

    @classmethod
    def from_str(cls, cmd: str) -> CommandABC:

        return cls.from_list(shlex.split(cmd))

    @classmethod
    def from_list(cls, cmd: List[str]) -> CommandABC:

        return cls([cmd])
