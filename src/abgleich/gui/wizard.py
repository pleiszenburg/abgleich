# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/gui/wizard.py: wizard gui

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

import os

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMessageBox
from typeguard import typechecked

from .transaction import TransactionListModel
from .wizard_base import WizardUiBase
from ..core.abc import ConfigABC
from ..core.transaction import TransactionList
from ..core.i18n import t
from ..core.zpool import Zpool
from .. import __version__

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@typechecked
class WizardUi(WizardUiBase):
    def __init__(self, config: ConfigABC):

        super().__init__()
        self._config = config

        self.setWindowIcon(
            QIcon(os.path.join(os.path.dirname(__file__), "..", "share", "icon.svg"))
        )
        self.setWindowTitle(f'{t("abgleich wizard"):s} {__version__:s}')

        self._ui["button_cancel"].setEnabled(False)
        self._ui["button_continue"].setEnabled(False)

        self._ui["button_cancel"].clicked.connect(self._cancel_click)
        self._ui["button_continue"].clicked.connect(self._continue_click)

        self._ui["button_cancel"].setText(t("Cancel"))
        self._ui["button_continue"].setText("")

        self._continue = lambda: None

        self._transactions = TransactionList()
        self._model = TransactionListModel(self._transactions, self._changed)
        self._ui["table"].setModel(self._model)

        self._steps = [
            {
                "init_button": t("Collect Snapshot Transactions"),
                "prepare": self._prepare_snap,
                "prepare_text": t("Collecting snapshot transactions ..."),
                "run_text": t("Creating snapshots ..."),
                "run_button": t("Execute Snapshot Transactions"),
                "finish_text": t("Snapshots created."),
                "finish_button": t("Collect Backup Transactions"),
            },
            {
                "prepare": lambda: self._prepare("backup"),
                "prepare_text": t("Collecting backup transactions ..."),
                "run_text": t("Transferring snapshots ..."),
                "run_button": t("Execute Backup Transactions"),
                "finish_text": t("Snapshots transferred."),
                "finish_button": t("Collect Cleanup Transactions"),
            },
            {
                "prepare": lambda: self._prepare("cleanup"),
                "prepare_text": t("Collecting cleanup transactions ..."),
                "run_text": t("Removing old snapshots ..."),
                "run_button": t("Execute Cleanup Transactions"),
                "finish_text": t("Old snapshots removed."),
                "finish_button": t("Close"),
            },
        ]

        self._init_step(0)

    def _changed(self):

        self._ui["table"].resizeColumnsToContents()
        QApplication.processEvents()

    def _continue_click(self):

        self._continue()

    def _cancel_click(self):

        self._quit()

    def _init_step(self, index: int):

        self._ui["button_cancel"].setEnabled(False)
        self._ui["button_continue"].setEnabled(False)
        self._ui["progress"].setValue(0)
        self._ui["label"].setText(self._steps[index]["prepare_text"])
        self._transactions.clear()

        if index > 0:
            self._prepare_step(index)
            return

        self._continue = lambda: self._prepare_step(index)
        self._ui["button_continue"].setText(self._steps[index]["init_button"])
        self._ui["button_cancel"].setEnabled(True)
        self._ui["button_continue"].setEnabled(True)

    def _prepare_step(self, index: int):

        self._ui["button_cancel"].setEnabled(False)
        self._ui["button_continue"].setEnabled(False)
        QApplication.processEvents()

        if not self._steps[index]["prepare"]():
            QMessageBox.warning(self, t("Warning"), t("Nothing to do."))
            self._finish_step(index)
            return

        self._ui["label"].setText(self._steps[index]["run_text"])
        self._continue = lambda: self._run_step(index)
        self._ui["button_continue"].setText(self._steps[index]["run_button"])
        self._ui["button_cancel"].setEnabled(True)
        self._ui["button_continue"].setEnabled(True)

    def _run_step(self, index: int):

        self._ui["button_cancel"].setEnabled(False)
        self._ui["button_continue"].setEnabled(False)
        self._ui["progress"].setMaximum(len(self._transactions))
        QApplication.processEvents()

        for number, transaction in enumerate(self._transactions):

            assert not transaction.running
            assert not transaction.complete

            transaction.run()
            self._ui["progress"].setValue(number + 1)
            QApplication.processEvents()

            assert not transaction.running
            assert transaction.complete

            if transaction.error is not None:
                QMessageBox.critical(
                    self,
                    t("Critical Error"),
                    t("Transaction failed!")
                    + "\n\n"
                    + "\n\n".join([str(item) for item in transaction.error.args]),
                )
                self._quit()
                return

        self._ui["label"].setText(self._steps[index]["finish_text"])
        self._continue = lambda: self._finish_step(index)

        if index + 1 == len(self._steps):
            self._ui["button_cancel"].setVisible(False)
        else:
            self._ui["button_cancel"].setEnabled(True)
        self._ui["button_continue"].setText(self._steps[index]["finish_button"])
        self._ui["button_continue"].setEnabled(True)

    def _finish_step(self, index: int):

        if index + 1 == len(self._steps):
            self._quit()
            return

        self._init_step(index + 1)

    def _prepare_snap(self):

        zpool = Zpool.from_config("source", config=self._config)

        gen = zpool.generate_snapshot_transactions()
        length, _ = next(gen)

        self._ui["progress"].setMaximum(length)
        QApplication.processEvents()

        for number, transaction in gen:
            if transaction is not None:
                self._transactions.append(transaction)
            self._ui["progress"].setValue(number + 1)
            QApplication.processEvents()

        return len(self._transactions) > 0

    def _prepare(self, action: str):

        source_zpool = Zpool.from_config("source", config=self._config)
        target_zpool = Zpool.from_config("target", config=self._config)

        gen = getattr(source_zpool, f"generate_{action:s}_transactions")(target_zpool)
        length, _ = next(gen)

        self._ui["progress"].setMaximum(length)
        QApplication.processEvents()

        for number, transactions in gen:
            if transactions is not None:
                self._transactions.extend(transactions)
            self._ui["progress"].setValue(number + 1)
            QApplication.processEvents()

        return len(self._transactions) > 0

    def _quit(self):

        self._transactions.clear()
        self.close()
