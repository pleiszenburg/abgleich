import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from docs.source.version import get_version

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "abgleich"
author = "Sebastian M. Ernst"
copyright = f"2019-2026 {author:s}"
release = get_version()

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
html_context = {
    "sidebar_external_links_caption": "Links",
    "sidebar_external_links": [
        # ('<i class="fa fa-rss fa-fw"></i> Blog', 'https://www.000'),
        (
            '<i class="fa fa-github fa-fw"></i> Source Code',
            "https://github.com/pleiszenburg/abgleich",
        ),
        (
            '<i class="fa fa-bug fa-fw"></i> Issue Tracker',
            "https://github.com/pleiszenburg/abgleich/issues",
        ),
        # ('<i class="fa fa-envelope fa-fw"></i> Mailing List', 'https://groups.io/g/abgleich-dev'),
        (
            '<i class="fa fa-comments fa-fw"></i> Chat',
            "https://matrix.to/#/#abgleich:matrix.org",
        ),
        # ('<i class="fa fa-file-text fa-fw"></i> Citation', 'https://doi.org/000'),
        (
            '<i class="fa fa-info-circle fa-fw"></i> pleiszenburg.de',
            "https://www.pleiszenburg.de/",
        ),
    ],
}
