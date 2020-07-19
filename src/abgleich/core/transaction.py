# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/core/transaction.py: ZFS transactions

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

from tabulate import tabulate
import typeguard

from .abc import CommandABC, TransactionABC, TransactionListABC, TransactionMetaABC
from .i18n import t
from .io import colorize, humanize_size

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@typeguard.typechecked
class Transaction(TransactionABC):
    def __init__(
        self, meta: TransactionMetaABC, commands: typing.List[CommandABC],
    ):

        assert len(commands) in (1, 2)

        self._meta, self._commands = meta, commands

        self._complete = False
        self._running = False
        self._error = None

        self._changed = None

    @property
    def changed(self) -> typing.Union[None, typing.Callable]:

        return self._changed

    @changed.setter
    def changed(self, value: typing.Union[None, typing.Callable]):

        self._changed = value

    @property
    def complete(self) -> bool:

        return self._complete

    @property
    def commands(self) -> typing.Tuple[CommandABC]:

        return self._commands

    @property
    def error(self) -> typing.Union[Exception, None]:

        return self._error

    @property
    def meta(self) -> TransactionMetaABC:

        return self._meta

    @property
    def running(self) -> bool:

        return self._running

    def run(self):

        if self._complete:
            return

        self._running = True
        if self._changed is not None:
            self._changed()

        try:
            if len(self._commands) == 1:
                output, errors = self._commands[0].run()
            else:
                errors_1, output_2, errors_2 = self._commands[0].run_pipe(
                    self._commands[1]
                )
        except SystemError as error:
            self._error = error
        finally:
            self._running = False
            self._complete = True
            if self._changed is not None:
                self._changed()


MetaTypes = typing.Union[str, int, float]
MetaNoneTypes = typing.Union[str, int, float, None]


@typeguard.typechecked
class TransactionMeta(TransactionMetaABC):
    def __init__(self, **kwargs: MetaTypes):

        self._meta = kwargs

    def __getitem__(self, key: str) -> MetaTypes:

        return self._meta[key]

    def __len__(self) -> int:

        return len(self._meta)

    def get(self, key: str) -> MetaNoneTypes:

        return self._meta.get(key, None)

    def keys(self) -> typing.Generator[str, None, None]:

        return (key for key in self._meta.keys())


TransactionIterableTypes = typing.Union[
    typing.Generator[TransactionABC, None, None],
    typing.List[TransactionABC],
    typing.Tuple[TransactionABC],
]


@typeguard.typechecked
class TransactionList(TransactionListABC):
    def __init__(self):

        self._transactions = []
        self._changed = None

    def __len__(self) -> int:

        return len(self._transactions)

    def __getitem__(self, index: int) -> TransactionABC:

        return self._transactions[index]

    @property
    def changed(self) -> typing.Union[None, typing.Callable]:

        return self._changed

    @changed.setter
    def changed(self, value: typing.Union[None, typing.Callable]):

        self._changed = value

    @property
    def table_columns(self) -> typing.List[str]:

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
    def table_rows(self) -> typing.List[str]:

        return [f'{t("transaction"):s} #{index:d}' for index in range(1, len(self) + 1)]

    def append(self, transaction: TransactionABC):

        self._transactions.append(transaction)
        if self._changed is not None:
            self._link_transaction(transaction)

    def extend(self, transactions: TransactionIterableTypes):

        transactions = list(transactions)
        self._transactions.extend(transactions)
        if self._changed is not None:
            for transaction in transactions:
                self._link_transaction(transaction)

    def clear(self):

        self._transactions.clear()
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
                table, headers=table_columns, tablefmt="github", colalign=colalign,
            )
        )

    @staticmethod
    def _table_format_cell(header: str, value: MetaNoneTypes) -> str:

        FORMAT = {
            t("written"): lambda v: humanize_size(v, add_color=True),
        }

        return FORMAT.get(header, str)(value)

    @staticmethod
    def _table_colalign(headers: typing.List[str]) -> typing.List[str]:

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
                f'{colorize(" | ".join([str(command) for command in transaction.commands]), "yellow"):s}'
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
