#!/home/thorsten/.local/share/virtualenvs/abgleich-uDwluHIz/bin/python
# -*- coding: utf-8 -*-

import re
import os
import sys
if __name__ == '__main__':
    sys.path.append(os.path.join(os.getcwd(),"src"))
from abgleich.cli import cli
if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    sys.exit(cli())
