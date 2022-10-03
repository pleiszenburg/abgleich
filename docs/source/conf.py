# -*- coding: utf-8 -*-

"""

ABGLEICH
zfs sync tool
https://github.com/pleiszenburg/abgleich

    docs/source/conf.py: Configures the documentation build process

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

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from docs.source.version import get_version

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'abgleich'
author = 'Sebastian M. Ernst'
copyright = f'2019-2022 {author:s}'
release = get_version()

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx_autodoc_typehints',
    'sphinx_rtd_theme',
    'myst_parser',
]

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_context = {
    'sidebar_external_links_caption': 'Links',
    'sidebar_external_links': [
        # ('<i class="fa fa-rss fa-fw"></i> Blog', 'https://www.000'),
        ('<i class="fa fa-github fa-fw"></i> Source Code', 'https://github.com/pleiszenburg/abgleich'),
        ('<i class="fa fa-bug fa-fw"></i> Issue Tracker', 'https://github.com/pleiszenburg/abgleich/issues'),
        # ('<i class="fa fa-envelope fa-fw"></i> Mailing List', 'https://groups.io/g/abgleich-dev'),
        ('<i class="fa fa-comments fa-fw"></i> Chat', 'https://matrix.to/#/#abgleich:matrix.org'),
        # ('<i class="fa fa-file-text fa-fw"></i> Citation', 'https://doi.org/000'),
        ('<i class="fa fa-info-circle fa-fw"></i> pleiszenburg.de', 'https://www.pleiszenburg.de/'),
    ],
}

always_document_param_types = True # sphinx_autodoc_typehints

napoleon_include_special_with_doc = True # napoleon
# napoleon_use_param = True
# napoleon_type_aliases = True
