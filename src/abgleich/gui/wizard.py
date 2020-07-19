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

from PyQt5.QtWidgets import QApplication
from typeguard import typechecked

from .transaction import TransactionListModel
from .wizard_base import WizardUiBase
from ..core.abc import ConfigABC
from ..core.transaction import TransactionList
from ..core.zpool import Zpool

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@typechecked
class WizardUi(WizardUiBase):
    def __init__(self, config: ConfigABC):

        super().__init__()
        self._config = config

        self._ui["button_cancel"].setEnabled(False)
        self._ui["button_continue"].setEnabled(False)

        self._ui["button_cancel"].clicked.connect(self._cancel_click)
        self._ui["button_continue"].clicked.connect(self._continue_click)

        self._ui["button_cancel"].setText("Cancel")
        self._ui["button_continue"].setText("Continue")

        self._continue = lambda: None

        self._transactions = TransactionList()
        self._model = TransactionListModel(self._transactions, self._changed)
        self._ui['table'].setModel(self._model)

        self._steps = [
            {
                'name': 'snap',
                'prepare': self._prepare_snap,
                'prepare_text': 'Collect snapshot tasks ...',
                'run_text': 'Create snapshots ...',
                'finish_text': 'Snapshots created.',
            },
            {
                'name': 'backup',
                'prepare': self._prepare_backup,
                'prepare_text': 'Collect backup tasks ...',
                'run_text': 'Transfer backups ...',
                'finish_text': 'Snapshots transferred.',
            },
            {
                'name': 'cleanup',
                'prepare': self._prepare_cleanup,
                'prepare_text': 'Collect cleanup tasks ...',
                'run_text': 'Remove old snapshots ...',
                'finish_text': 'Old snapshots removed.',
            },
        ]

        self._init_step(0)

    def _changed(self):

        self._ui['table'].resizeColumnsToContents()
        QApplication.processEvents()

    def _continue_click(self):

        self._continue()

    def _cancel_click(self):

        self.close()

    def _init_step(self, index: int):

        self._ui["button_cancel"].setEnabled(False)
        self._ui["button_continue"].setEnabled(False)
        self._ui['progress'].setValue(0)
        self._ui['label'].setText(self._steps[index]['prepare_text'])
        self._transactions.clear()
        self._continue = lambda: self._prepare_step(index)
        self._ui["button_cancel"].setEnabled(True)
        self._ui["button_continue"].setEnabled(True)

    def _prepare_step(self, index: int):

        self._ui["button_cancel"].setEnabled(False)
        self._ui["button_continue"].setEnabled(False)
        QApplication.processEvents()
        self._steps[index]['prepare']()
        self._ui['label'].setText(self._steps[index]['run_text'])
        self._continue = lambda: self._run_step(index)
        self._ui["button_cancel"].setEnabled(True)
        self._ui["button_continue"].setEnabled(True)

    def _run_step(self, index: int):

        self._ui["button_cancel"].setEnabled(False)
        self._ui["button_continue"].setEnabled(False)
        self._ui['progress'].setMaximum(len(self._transactions))
        QApplication.processEvents()

        for number, transaction in enumerate(self._transactions):

            assert not transaction.running
            assert not transaction.complete

            transaction.run()
            self._ui['progress'].setValue(number + 1)
            QApplication.processEvents()

            assert not transaction.running
            assert transaction.complete

            if transaction.error is not None:
                raise transaction.error # TODO

        self._ui['label'].setText(self._steps[index]['finish_text'])
        self._continue = lambda: self._finish_step(index)
        self._ui["button_cancel"].setEnabled(True)
        self._ui["button_continue"].setEnabled(True)

    def _finish_step(self, index: int):

        if index + 1 == len(self._steps):
            self.close() # TODO

        self._init_step(index + 1)

    def _prepare_snap(self):

        zpool = Zpool.from_config("source", config=self._config)

        gen = zpool.generate_snapshot_transactions()
        length, _ = next(gen)

        self._ui['progress'].setMaximum(length)
        QApplication.processEvents()

        for number, transaction in gen:
            if transaction is not None:
                self._transactions.append(transaction)
            self._ui['progress'].setValue(number + 1)
            QApplication.processEvents()

    def _prepare_backup(self):

        source_zpool = Zpool.from_config("source", config=self._config)
        target_zpool = Zpool.from_config("target", config=self._config)

        gen = source_zpool.generate_backup_transactions(target_zpool)
        length, _ = next(gen)

        self._ui['progress'].setMaximum(length)
        QApplication.processEvents()

        for number, transactions in gen:
            if transactions is not None:
                self._transactions.extend(transactions)
            self._ui['progress'].setValue(number + 1)
            QApplication.processEvents()

    def _prepare_cleanup(self):

        pass
