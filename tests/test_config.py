# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

	tests/test_config.py: Configuration module tests

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
# CONST
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

RAW = """always_changed: false
check_diff: false
digits: 2
ignore:
- CACHE
- CACHE_CC
- CACHE_THUMBNAILS
- DESKTOP/SCRATCH
include_root: true
keep_backlog: true
keep_snapshots: 2
source:
    host: sourcehost
    prefix: sourceprefix
    zpool: sourcepool
ssh:
    cipher: aes256-gcm@openssh.com
    compression: false
suffix: _backup
target:
    host: targethost
    prefix: targetprefix
    user: targetuser
    zpool: targetpool
written_threshold: 1048576
"""

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# IMPORT
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

from deepdiff import DeepDiff

from abgleich import Config

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ROUTINES
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


def test_importexport():

    c = Config.from_text(RAW)
    raw = c.to_text()

    assert RAW == raw

    d = Config.from_text(raw)

    assert DeepDiff(c, d, ignore_order=True) == {}
