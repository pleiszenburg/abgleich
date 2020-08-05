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

import subprocess
import typing

import typeguard

from .abc import CommandABC

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@typeguard.typechecked
class Command(CommandABC):
    def __init__(self, cmd: typing.List[str]):

        self._cmd = cmd.copy()

    def __str__(self) -> str:

        return " ".join([item.replace(" ", "\\ ") for item in self._cmd])

    def run(
        self, returncode: bool = False
    ) -> typing.Union[typing.Tuple[str, str], typing.Tuple[str, str, int, Exception]]:

        proc = subprocess.Popen(
            self.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        output, errors = proc.communicate()
        status = not bool(proc.returncode)
        output, errors = output.decode("utf-8"), errors.decode("utf-8")

        exception = SystemError("command failed", str(self), output, errors)

        if returncode:
            return output, errors, int(proc.returncode), exception

        if not status or len(errors.strip()) > 0:
            raise exception

        return output, errors

    def run_pipe(self, other: CommandABC):

        proc_1 = subprocess.Popen(
            self.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        proc_2 = subprocess.Popen(
            other.cmd,
            stdin=proc_1.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        output_2, errors_2 = proc_2.communicate()
        status_2 = not bool(proc_2.returncode)
        _, errors_1 = proc_1.communicate()
        status_1 = not bool(proc_1.returncode)

        errors_1 = errors_1.decode("utf-8")
        output_2, errors_2 = output_2.decode("utf-8"), errors_2.decode("utf-8")

        if any(
            (
                not status_1,
                len(errors_1.strip()) > 0,
                not status_2,
                len(errors_2.strip()) > 0,
            )
        ):
            raise SystemError(
                "command pipe failed",
                f"{str(self):s} | {str(other):s}",
                errors_1,
                output_2,
                errors_2,
            )

        return errors_1, output_2, errors_2

    @property
    def cmd(self) -> typing.List[str]:

        return self._cmd.copy()

    @classmethod
    def on_side(
        cls, cmd: typing.List[str], side: str, config: typing.Dict
    ) -> CommandABC:

        if config[side]["host"] == "localhost":
            return cls(cmd)
        return cls.with_ssh(cmd, side_config=config[side], ssh_config=config["ssh"])

    @classmethod
    def with_ssh(
        cls, cmd: typing.List[str], side_config: typing.Dict, ssh_config: typing.Dict
    ) -> CommandABC:

        cmd_str = " ".join([item.replace(" ", "\\ ") for item in cmd])
        cmd = [
            "ssh",
            "-T",  # Disable pseudo-terminal allocation
            "-o",
            "Compression=yes" if ssh_config["compression"] else "Compression=no",
        ]
        if ssh_config["cipher"] is not None:
            cmd.extend(("-c", ssh_config["cipher"]))
        cmd.extend([f'{side_config["user"]:s}@{side_config["host"]:s}', cmd_str])

        return cls(cmd)
