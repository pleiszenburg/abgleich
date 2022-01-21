# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/core/transactionlist.py: ZFS transaction list

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

from typing import Callable, Generator, List, Union

from tabulate import tabulate
from typeguard import typechecked

from .abc import TransactionABC, TransactionListABC
from .i18n import t
from .io import colorize, humanize_size
from .transactionmeta import TransactionMetaTypes

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@typechecked
class TransactionList(TransactionListABC):
    """
    Mutable.
    """

    def __init__(self, *transactions: TransactionABC):

        self._transactions = list(transactions)
        self._changed = None

    def __len__(self) -> int:

        return len(self._transactions)

    def __add__(self, other: TransactionListABC) -> TransactionListABC:

        return type(self)(*(tuple(self.transactions) + tuple(other.transactions)))

    def __getitem__(self, index: int) -> TransactionABC:

        return self._transactions[index]

    @property
    def changed(self) -> Union[None, Callable]:

        return self._changed

    @changed.setter
    def changed(self, value: Union[None, Callable]):

        self._changed = value

    @property
    def table_columns(self) -> List[str]:

        headers = set()
        for transaction in self._transactions:
            keys = list(transaction.meta.keys())
            assert t("type") in keys
            headers.update(keys)
        headers = list(headers)
        headers.sort()

        if len(headers) == 0:
            return headers

        type_index = headers.index(t("type"))
        if type_index != 0:
            headers.pop(type_index)
            headers.insert(0, t("type"))

        return headers

    @property
    def table_rows(self) -> List[str]:

        return [f'{t("transaction"):s} #{index:d}' for index in range(1, len(self) + 1)]

    @property
    def transactions(self) -> Generator[TransactionABC, None, None]:

        return (transaction for transaction in self._transactions)

    def append(self, transaction: TransactionABC):

        self._transactions.append(transaction)
        if self._changed is not None:
            self._link_transaction(transaction)

    def extend(self, transactions: TransactionListABC):

        transactions = list(transactions.transactions)
        self._transactions.extend(transactions)
        if self._changed is not None:
            for transaction in transactions:
                self._link_transaction(transaction)

    def clear(self):

        self._transactions.clear()
        if self._changed is not None:
            self._changed()

    def _link_transaction(self, transaction: TransactionABC):

        transaction.changed = lambda: self._changed(
            self._transactions.index(transaction)
        )
        transaction.changed()

    def print_table(self):

        if len(self) == 0:
            return

        table_columns = self.table_columns
        colalign = self._table_colalign(table_columns)

        table = [
            [
                self._table_format_cell(header, transaction.meta.get(header))
                for header in table_columns
            ]
            for transaction in self._transactions
        ]

        print(
            tabulate(
                table,
                headers=table_columns,
                tablefmt="github",
                colalign=colalign,
            )
        )

    @staticmethod
    def _table_format_cell(
        header: str, value: Union[TransactionMetaTypes, None]
    ) -> str:

        FORMAT = {
            t("written"): lambda v: humanize_size(v, add_color=True),
        }

        return FORMAT.get(header, str)(value)

    @staticmethod
    def _table_colalign(headers: List[str]) -> List[str]:

        RIGHT = (t("written"),)
        DECIMAL = tuple()

        colalign = []
        for header in headers:
            if header in RIGHT:
                colalign.append("right")
            elif header in DECIMAL:
                colalign.append("decimal")
            else:
                colalign.append("left")

        return colalign

    def run(self):

        for transaction in self._transactions:

            print(
                f'({colorize(transaction.meta[t("type")], "white"):s}) '
                f'{colorize(str(transaction.command), "yellow"):s}'
            )

            assert not transaction.running
            assert not transaction.complete

            transaction.run()

            assert not transaction.running
            assert transaction.complete

            if transaction.error is not None:
                print(colorize(t("FAILED"), "red"))
                raise transaction.error
            else:
                print(colorize(t("OK"), "green"))
