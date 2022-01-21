# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/core/transaction.py: ZFS transactions

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

from typing import Callable, Union

from typeguard import typechecked

from .abc import CommandABC, ConfigABC, PropertyABC, TransactionABC, TransactionMetaABC
from .command import Command
from .i18n import t
from .transactionmeta import TransactionMeta


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@typechecked
class Transaction(TransactionABC):
    """
    Mutable.
    """

    def __init__(
        self,
        meta: TransactionMetaABC,
        command: CommandABC,
    ):

        self._meta, self._command = meta, command

        self._complete = False
        self._running = False
        self._error = None

        self._changed = None

    @property
    def changed(self) -> Union[None, Callable]:

        return self._changed

    @changed.setter
    def changed(self, value: Union[None, Callable]):

        self._changed = value

    @property
    def complete(self) -> bool:

        return self._complete

    @property
    def command(self) -> CommandABC:

        return self._command

    @property
    def error(self) -> Union[Exception, None]:

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
            _, _ = self._command.run()
        except SystemError as error:
            self._error = error
        finally:
            self._running = False
            self._complete = True
            if self._changed is not None:
                self._changed()

    @classmethod
    def set_property(
        cls,
        item: str,
        property: PropertyABC,
        side: str,
        config: ConfigABC,
    ) -> TransactionABC:

        return cls(
            meta=TransactionMeta(
                **{
                    t("type"): t("set_property"),
                    t("item"): item,
                }
            ),
            command=Command.from_list(
                [
                    "zfs",
                    "set",
                    f"{property.name:s}={property.value_export:s}",
                    item,
                ]
            ).on_side(side=side, config=config),
        )
