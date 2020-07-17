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

from typeguard import typechecked

from .wizard_base import WizardUiBase
from ..core.abc import ConfigABC

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

    def _continue_click(self):

        pass

    def _cancel_click(self):

        pass
