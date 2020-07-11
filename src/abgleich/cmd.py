# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

	src/abgleich/cmd.py: Subprocess wrappers

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

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ROUTINES
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


def run_command(cmd_list, debug=False):
    if debug:
        print_commands(cmd_list)
        return
    proc = subprocess.Popen(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    outs, errs = proc.communicate()
    status_value = not bool(proc.returncode)
    output, errors = outs.decode("utf-8"), errs.decode("utf-8")
    if len(errors.strip()) != 0 or not status_value:
        print(output)
        print(errors)
        raise
    return output


def run_chain_command(cmd_list_1, cmd_list_2, debug=False):
    if debug:
        print_commands(cmd_list_1, cmd_list_2)
        return
    proc_1 = subprocess.Popen(
        cmd_list_1, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    proc_2 = subprocess.Popen(
        cmd_list_2, stdin=proc_1.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    outs_2, errs_2 = proc_2.communicate()
    status_value_2 = not bool(proc_2.returncode)
    _, errs_1 = proc_1.communicate()
    status_value_1 = not bool(proc_1.returncode)
    output_2, errors_2 = outs_2.decode("utf-8"), errs_2.decode("utf-8")
    errors_1 = errs_1.decode("utf-8")
    if any(
        [
            len(errors_1.strip()) != 0,
            not status_value_1,
            len(errors_2.strip()) != 0,
            not status_value_2,
        ]
    ):
        print(errors_1)
        print(output_2)
        print(errors_2)
        raise
    return output_2


def print_commands(*args):
    commands = [" ".join(cmd_list) for cmd_list in args]
    print("#> " + " | ".join(commands))


def ssh_command(host, cmd_list, compression=False):
    return get_ssh_prefix(compression) + [
        host,
        " ".join([item.replace(" ", "\\ ") for item in cmd_list]),
    ]


def get_ssh_prefix(compression=False):
    return [
        "ssh",
        "-T",
        "-c",
        "aes256-gcm@openssh.com",
        "-o",
        "Compression=yes" if compression else "Compression=no",
    ]
