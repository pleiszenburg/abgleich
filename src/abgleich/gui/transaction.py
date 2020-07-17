# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/gui/transaction.py: ZFS transactions

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
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt

from ..core.abc import TransactionListABC

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@typeguard.typechecked
class TransactionListModel(QAbstractTableModel):

    def __init__(self, transactions: TransactionListABC):

        super().__init__()
        self._transactions = transactions
        self._transactions.changed = self._changed

        self._rows, self._cols = None, None
        self._update()

    def data(self, index: QModelIndex, role: int) -> typing.Union[None, str]: # TODO return type

        row, col = index.row(), index.column()
        col_key = self._cols[col]

        if role == Qt.DisplayRole:
            if col_key != 'status':
                return str(self._transactions[row].meta[col_key]) # TODO format ...
            else:
                return 'no idea' # TODO actual

    def headerData(self, section: int, orientation: Qt.Orientation, role: int) -> typing.Union[None, str]:

        if role == Qt.DisplayRole:

            if orientation == Qt.Horizontal:
                return self._cols[section]

            if orientation == Qt.Vertical:
                return self._rows[section]

    def rowCount(self, index: QModelIndex) -> int:

        return len(self._transactions)

    def columnCount(self, index: QModelIndex) -> int:

        return len(self._cols)

    def _changed(self):

        self._update()
        self.layoutChanged.emit()
        # self.model.dataChanged.emit(index, index)

    def _update(self):

        self._rows = self._transactions.table_rows
        self._cols = self._transactions.table_columns
        self._cols.append('status')