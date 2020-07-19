# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/core/io.py: Command line IO

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

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CONSTANTS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# https://en.wikipedia.org/wiki/ANSI_escape_code
c = {
    "RESET": "\033[0;0m",
    "BOLD": "\033[;1m",
    "REVERSE": "\033[;7m",
    "GREY": "\033[1;30m",
    "RED": "\033[1;31m",
    "GREEN": "\033[1;32m",
    "YELLOW": "\033[1;33m",
    "BLUE": "\033[1;34m",
    "MAGENTA": "\033[1;35m",
    "CYAN": "\033[1;36m",
    "WHITE": "\033[1;37m",
}


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ROUTINES
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@typeguard.typechecked
def colorize(text: str, col: str) -> str:
    return c.get(col.upper(), c["GREY"]) + text + c["RESET"]


@typeguard.typechecked
def humanize_size(
    size: typing.Union[float, int], add_color: bool = False, get_rgb: bool = False
) -> str:

    suffix = "B"

    for unit, color, rgb in (
        ("", "cyan", "#0000FF"),
        ("Ki", "green", "#00FF00"),
        ("Mi", "yellow", "#FFFF00"),
        ("Gi", "red", "#FF0000"),
        ("Ti", "magenta", "#FF00FF"),
        ("Pi", "white", "#FFFFFF"),
        ("Ei", "white", "#FFFFFF"),
        ("Zi", "white", "#FFFFFF"),
        ("Yi", "white", "#FFFFFF"),
    ):
        if abs(size) < 1024.0:
            if get_rgb:
                return rgb
            text = "%3.1f %s%s" % (size, unit, suffix)
            if add_color:
                text = colorize(text, color)
            return text
        size /= 1024.0

    raise ValueError('"size" too large')
