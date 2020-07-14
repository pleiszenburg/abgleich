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

    def __len__(self) -> int:

        return len(self._transactions)

    def append(self, transaction: TransactionABC):

        self._transactions.append(transaction)

    def extend(self, transactions: TransactionIterableTypes):

        self._transactions.extend(transactions)

    def print_table(self):

        if len(self) == 0:
            return

        headers = self._table_headers()
        colalign = self._table_colalign(headers)

        table = [
            [
                self._table_format_cell(header, transaction.meta.get(header))
                for header in headers
            ]
            for transaction in self._transactions
        ]

        print(tabulate(table, headers=headers, tablefmt="github", colalign=colalign,))

    @staticmethod
    def _table_format_cell(header: str, value: MetaNoneTypes) -> str:

        FORMAT = {
            "written": lambda v: humanize_size(v, add_color=True),
        }

        return FORMAT.get(header, str)(value)

    @staticmethod
    def _table_colalign(headers: typing.List[str]) -> typing.List[str]:

        RIGHT = ("written",)
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

    def _table_headers(self) -> typing.List[str]:

        headers = set()
        for transaction in self._transactions:
            keys = list(transaction.meta.keys())
            assert "type" in keys
            headers.update(keys)
        headers = list(headers)
        headers.sort()

        type_index = headers.index("type")
        if type_index != 0:
            headers.pop(type_index)
            headers.insert(0, "type")

        return headers

    def run(self):

        for transaction in self._transactions:

            print(
                f'({colorize(transaction.meta["type"], "white"):s}) '
                f'{colorize(" | ".join([str(command) for command in transaction.commands]), "yellow"):s}'
            )

            assert not transaction.running
            assert not transaction.complete

            transaction.run()

            assert not transaction.running
            assert transaction.complete

            if transaction.error is not None:
                print(colorize("FAILED", "red"))
                raise transaction.error
            else:
                print(colorize("OK", "green"))
