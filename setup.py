# -*- coding: utf-8 -*-

"""

ABGLEICH
btrfs and zfs sync tool
https://github.com/pleiszenburg/abgleich

	setup.py: Used for package distribution

	Copyright (C) 2019 Sebastian M. Ernst <ernst@pleiszenburg.de>

<LICENSE_BLOCK>
Proprietary.
</LICENSE_BLOCK>

"""

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# IMPORT
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

from setuptools import (
	find_packages,
	setup,
	)
import os

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# SETUP
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# Package version
__version__ = '0.0.1'

# List all versions of Python which are supported
confirmed_python_versions = [
	('Programming Language :: Python :: %s' % x)
	for x in '3.6 3.7'.split(' ')
	]

# Fetch readme file
with open(os.path.join(os.path.dirname(__file__), 'README.md')) as f:
	long_description = f.read()

# Define source directory (path)
SRC_DIR = 'src'

# Install package
setup(
	name = 'abgleich',
	packages = find_packages(SRC_DIR),
	package_dir = {'': SRC_DIR},
	version = __version__,
	description = 'btrfs and zfs sync tool',
	long_description = long_description,
	long_description_content_type = 'text/markdown',
	author = 'Sebastian M. Ernst',
	author_email = 'ernst@pleiszenburg.de',
	url = 'https://github.com/pleiszenburg/abgleich',
	download_url = 'https://github.com/pleiszenburg/abgleich/archive/v%s.tar.gz' % __version__,
	license = 'proprietary',
	keywords = [
		'btrfs',
		'zfs',
		'ssh',
		],
	scripts = [],
	include_package_data = True,
	setup_requires = [],
	install_requires = [
		'click',
		'tabulate',
		],
	extras_require = {'dev': [
		# 'pytest',
		'python-language-server',
		'setuptools',
		# 'Sphinx',
		# 'sphinx_rtd_theme',
		'twine',
		'wheel',
		]},
	zip_safe = False,
	entry_points = {
		'console_scripts': [
			'abgleich = abgleich.cli:cli',
			],
		},
	classifiers = [
		'Development Status :: 3 - Alpha',
		'Environment :: Console',
		'Intended Audience :: Education',
		'Intended Audience :: Science/Research',
		'Operating System :: MacOS',
		'Operating System :: POSIX :: BSD',
		'Operating System :: POSIX :: Linux',
		'Programming Language :: Python :: 3'
		] + confirmed_python_versions + [
		'Programming Language :: Python :: 3 :: Only',
		'Topic :: Education',
		'Topic :: Scientific/Engineering',
		]
	)
