# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/zfs/transaction.py: ZFS transactions

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

from .abc import TransactionABC, TransactionListABC
from ..abc import CommandABC

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@typeguard.typechecked
class Transaction(TransactionABC):

    def __init__(
        self,
        description: str,
        commands: typing.Tuple[CommandABC],
    ):

        assert len(commands) in (1, 2)

        self._description, self._commands = description, commands

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
    def description(self) -> str:

        return self._description

    @property
    def error(self) -> typing.Union[Exception, None]:

        return self._error

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
                output_1, errors_1, output_2, errors_2 = self._commands[0].run_pipe(self._commands[1])
        except SystemError as error:
            self._error = error
        finally:
            self._running = False
            self._complete = True

@typeguard.typechecked
class TransactionList(TransactionListABC):

    def __init__(self):

        self._transactions = []

    def append(self, transaction: TransactionABC):

        self._transactions.append(transaction)
