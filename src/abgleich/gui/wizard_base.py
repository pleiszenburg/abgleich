# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/gui/wizard_base.py: wizard gui base

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

from PyQt5.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout
from typeguard import typechecked

from .abc import WizardUiBaseABC

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@typechecked
class WizardUiBase(WizardUiBaseABC, QDialog):

    def __init__(self):

        super(WizardUiBaseABC, self).__init__() # skip WizardUiBaseABC

        self.setWindowTitle('Wizard')

        self._ui_dict = {
            'layout_0_v_root': QVBoxLayout(), # dialog
            'layout_1_h_buttoms': QHBoxLayout(), # for buttons
            }
        self.setLayout(self._ui_dict['layout_0_v_root'])

        # self._ui_dict['layout_0_v_root'].addLayout(self._ui_dict['layout_1_h_buttoms'])
