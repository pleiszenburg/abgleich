:github_url:

.. _bugs:

.. index::
	triple: bug; issue; report
	triple: bug; issue; bisect

Bugs & Known Issues
===================

Please report bugs in *abgleich*'s `GitHub issue tracker`_.

.. _GitHub issue tracker: https://github.com/pleiszenburg/abgleich/issues

How to bisect issues
--------------------

You can activate additional debugging features intended for developers by setting the ``ABGLEICH_DEBUG`` environment variable to ``1`` before running *abgleich*. For this to work, the `typeguard package`_ must be present on your system.

.. _typeguard package: https://typeguard.readthedocs.io/

Translations
------------

*abgleich* can be translated, i.e. it allows internationalization / i18n. Currently, next to English, German is also offered. *abgleich* detects the system language during its start and attempts to display all of its messages accordingly. If no translation can be provided for a given message, *abgleich* falls back to English. Translations can be added or corrected by editing `translations.yaml`_. If a string is completely missing from ``translations.yaml`` even in its primary language, English, one can run *abgleich* with the ``ABGLEICH_TRANSLATE`` environment variable set to ``1``. This activates a mechanism that automatically adds missing strings to ``translations.yaml`` whenever they are encountered while running *abgleich*.

.. _translations.yaml: https://github.com/pleiszenburg/abgleich/blob/develop/src/abgleich/share/translations.yaml
