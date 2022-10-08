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

You can activate additional debugging features intended for developers by setting the ``ABGLEICH_DEBUG`` environment variable to ``1`` before running ``abgleich``. For this to work, the `typeguard package`_ must be present on your system.

.. _typeguard package: https://typeguard.readthedocs.io/
