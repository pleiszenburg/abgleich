Installation
============

Prerequisites
-------------

There are anywhere from one to three systems with the following distinct characteristics:

1) Running ``abgleich``.
2) The location of the ``source`` zpool.
3) The location of the ``target`` zpool.

On the system that is running ``abgleich`` itself, ``python3`` (`CPython`_ 3.6 or later) and ``ssh`` is required. ``abgleich`` can be operated both from the ``source`` and the ``target`` side but also from a third, otherwise unrelated system. In addition, both the ``source`` and the ``target`` side must provide a shell as well as ``ssh`` next to ``ZFS`` drivers and at least one zpool. ``source`` and ``target`` can be on the same system if two local zpools are supposed to be synchronized.

.. _CPython: https://en.wikipedia.org/wiki/CPython

.. note::

    If everything happens on a single system, no ``ssh`` is required.

On Debian/Ubuntu-based systems, all potentially required prerequisites other than ZFS can be installed as follows:

.. code:: bash

    sudo apt install python3 python3-venv openssh

.. warning::

    It is strongly recommended to operate ``abgleich`` with user privileges only.

It is recommended to created dedicated user accounts on all involved systems and to grant them specific rights only. If operations must be triggered on remote systems, `public key authentication must be configured`_ for ``ssh`` for the relevant user accounts on all involved machines. For additional details, see man pages of `ssh-keygen`_ and `ssh`_ itself.

.. _public key authentication must be configured: https://help.ubuntu.com/community/SSH/OpenSSH/Keys
.. _ssh-keygen: https://linux.die.net/man/1/ssh-keygen
.. _ssh: https://linux.die.net/man/1/ssh

In addition, the following ZFS operations must be allowed for the user on the following sides:

+------------------+--------+--------+
| command          | source | target |
+==================+========+========+
| ``zfs create``   |        |    x   |
+------------------+--------+--------+
| ``zfs destroy``  |    x   |        |
+------------------+--------+--------+
| ``zfs diff``     |    x   |        |
+------------------+--------+--------+
| ``zfs mount``    |    x   |    x   |
+------------------+--------+--------+
| ``zfs receive``  |        |    x   |
+------------------+--------+--------+
| ``zfs send``     |    x   |        |
+------------------+--------+--------+
| ``zfs snapshot`` |    x   |        |
+------------------+--------+--------+

Relevant ZFS operations on the ``source`` side can be allowed for user ``username`` as follows:

.. code:: bash

    sudo zfs allow username destroy,diff,mount,send,snapshot sourcepool

Relevant ZFS operations on the ``target`` side can be allowed for user ``username`` as follows:

.. code:: bash

    sudo zfs allow username create,mount,receive targetpool

For more details, see `man page for ZFS allow`_.

.. _man page for ZFS allow: https://openzfs.github.io/openzfs-docs/man/8/zfs-allow.8.html

Getting ``abgleich``
--------------------

``abgleich`` can be installed and updated via Python's package manager `pip`_.

.. warning::

    Installation into a Python `virtual environment`_ is strongly recommended. The creation of virtual environments as well as the installation Python packages into them with ``pip`` is typically performed with user privileges only.

.. _pip: https://pip.pypa.io/en/stable/
.. _virtual environment: https://docs.python.org/3/library/venv.html

A basic installation workflow may look as follows:

.. code:: bash

    python3 -m venv env  # create a virtual environment named "env" within CWD
    source env/bin/activate  # activate virtual environment named "env" within CWD
    pip install -U setuptools pip  # update Python's pip and setuptools
    pip install abgleich  # install abgleich itself

An installation also including a :ref:`GUI <gui>` can be triggered by running:

.. code:: bash

    pip install abgleich[gui]

You can check your installation by running:

.. code:: bash

    abgleich --help

.. note::

    If ``abgleich`` was installed into a virtual environment, this virtual environment must be explicitly activated for each particular shell session prior to using any of ``abgleich``'s commands.

.. note::

    If you are relying on *abgleich*, please notice that it uses **semantic versioning**. Breaking changes are indicated by increasing the second version number, the minor version. Going for example from ``0.0.x`` to ``0.1.y`` or going from ``0.1.x`` to ``0.2.y`` therefore indicates a breaking change. For as long as *abgleich* has development status "alpha", please expect more breaking changes to come.

Upgrading ``abgleich``
----------------------

With the relevant virtual environment activated, run:

.. code:: bash

    pip install -U abgleich

.. note::

	If you are relying on *abgleich*, please notice that it uses **semantic versioning**. Breaking changes are indicated by increasing the second version number, the minor version. Going for example from ``0.0.x`` to ``0.1.y`` or going from ``0.1.x`` to ``0.2.y`` therefore indicates a breaking change. For as long as *abgleich* has development status "alpha", please expect more breaking changes to come.
