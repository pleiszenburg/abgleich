# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/core/abc.py: Abstract base classes

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

import abc

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASSES
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


class CloneABC(abc.ABC):
    pass


class CommandABC(abc.ABC):
    pass


class ComparisonABC(abc.ABC):
    pass


class ComparisonItemABC(abc.ABC):
    pass


class ConfigABC(abc.ABC):
    pass


class DatasetABC(abc.ABC):
    pass


class PropertyABC(abc.ABC):
    pass


class SnapshotABC(abc.ABC):
    pass


class TransactionABC(abc.ABC):
    pass


class TransactionListABC(abc.ABC):
    pass


class TransactionMetaABC(abc.ABC):
    pass


class ZpoolABC(abc.ABC):
    pass
