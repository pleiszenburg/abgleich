# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/core/abc.py: Abstract base classes

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

from abc import ABC

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASSES
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


class CloneABC(ABC):
    pass


class CommandABC(ABC):
    pass


class ComparisonDatasetABC(ABC):
    pass


class ComparisonItemABC(ABC):
    pass


class ComparisonZpoolABC(ABC):
    pass


class ConfigABC(ABC):
    pass


class ConfigFieldABC(ABC):
    pass


class DatasetABC(ABC):
    pass


class PropertyABC(ABC):
    pass


class SnapshotABC(ABC):
    pass


class TransactionABC(ABC):
    pass


class TransactionListABC(ABC):
    pass


class TransactionMetaABC(ABC):
    pass


class ZpoolABC(ABC):
    pass
