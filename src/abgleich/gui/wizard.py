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
        self._transactions = None
        self._model = None
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

    def _continue_click(self):

        self._continue()

    def _cancel_click(self):

        self.close()

    def _init_step(self, index: int):

        self._ui['label'].setText(self._steps[index]['prepare_text'])
        self._transactions = TransactionList()
        self._model = TransactionListModel(self._transactions)
        self._ui['table'].setModel(self._model)
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

        pass

    def _finish_step(self, index: int):

        pass

    def _prepare_snap(self):

        zpool = Zpool.from_config("source", config=self._config)
        zpool.get_snapshot_transactions(self._transactions)

    def _prepare_backup(self):

        pass

    def _prepare_cleanup(self):

        pass
