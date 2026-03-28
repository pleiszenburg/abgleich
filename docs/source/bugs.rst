:github_url:

.. _bugs:

.. index::
	triple: bug; issue; report
	triple: bug; issue; bisect

Bugs & Known Issues
===================

Please report bugs in *abgleich*'s `GitHub issue tracker`_. Add the version of ``abgleich`` to all reports, i.e. ``abgleich --version``.

.. _GitHub issue tracker: https://github.com/pleiszenburg/abgleich/issues

How to bisect issues
--------------------

You can activate additional debugging features intended for developers by setting the ``ABGLEICH_LOGLEVEL`` environment variable to ``0`` before running *abgleich*.

Known Issue: The Property Parser
--------------------------------

Properties of ZFS datasets and snapshots are extracted by ``abgleich`` by running:

.. code:: bash

    zfs get -Hp all dataset  # specifically one dataset
    zfs get -rHp all dataset  # dataset and all descendants recursively

Although the property parser in ``abgleich`` has been extensively tested, there can be false assumptions about data types and default values, effectively breaking the application. For security purposes, ``abgleich`` throws an exception and exits if it encounters an unexpected value, without any further actions taken. If you observe such an issue, please provide the output of the above ZFS commands for verification.
