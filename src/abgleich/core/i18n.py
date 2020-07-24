# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    src/abgleich/core/i18n.py: Translations

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

import locale
import os

import typeguard
import yaml

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import FullLoader as Loader

try:
    from yaml import CDumper as Dumper
except ImportError:
    from yaml import Dumper

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@typeguard.typechecked
class _Lang(dict):
    def __init__(self):

        super().__init__()
        self._lang = locale.getlocale()[0].split("_")[0]
        self._path = os.path.join(
            os.path.dirname(__file__), "..", "share", "translations.yaml"
        )
        self._load()

    def __call__(self, name: str) -> str:

        assert len(name) > 0

        if int(os.environ.get("ABGLEICH_TRANSLATE", "0")) == 1:
            if name not in self.keys():
                self._add_item(name)

        return self.get(name, {}).get(self._lang, name)

    def _add_item(self, name: str):

        self[name] = {}
        self._dump()

    def _load(self):

        self.clear()

        with open(self._path, "r") as f:
            self.update(yaml.load(f.read(), Loader=Loader))

    def _dump(self):

        with open(self._path, "w") as f:
            f.write(yaml.dump(self.copy(), Dumper=Dumper, allow_unicode=True, indent=4))


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# API
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

t = _Lang()
