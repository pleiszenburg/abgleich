.. _installation:

Installation
============

Getting ``abgleich``
--------------------

``abgleich`` is written in Rust and can be statically linked against `musl`_, allowing self-contained portable binaries, trivial deployment and maximum compatibility. The primary target platforms are **Linux** and **FreeBSD** on x86_64. Both x86 (32 bit) and ARM support are theoretically trivial but currently untested territory - pull requests welcome. ``abgleich`` does not need to run on any remotely accessed target system, only the box where it actually gets invoked.

.. _musl: https://en.wikipedia.org/wiki/Musl

Pre-Built Binaries
^^^^^^^^^^^^^^^^^^

Pre-built binaries for Linux and FreeBSD can be found on the `releases page`_.

.. _releases page: https://github.com/pleiszenburg/abgleich/releases

You can use the following command on Linux or FreeBSD to download the latest release. Simply replace ``DEST`` with the directory where you would like to put ``abgleich``:

.. code:: bash

    curl --proto '=https' --tlsv1.2 -sSf https://abgleich.pleiszenburg.de/install.sh | bash -s -- --to DEST

For example, to install ``abgleich`` to ``~/bin``:

.. code:: bash

    # create ~/bin
    mkdir -p ~/bin

    # download and extract abgleich to ~/bin/abgleich
    curl --proto '=https' --tlsv1.2 -sSf https://abgleich.pleiszenburg.de/install.sh | bash -s -- --to ~/bin

    # add `~/bin` to the paths that your shell searches for executables
    # this line should be added to your shells initialization file,
    # e.g. `~/.bashrc` or `~/.zshrc`
    export PATH="$PATH:$HOME/bin"

You can check your installation by running:

.. code:: bash

    abgleich --help

Optional: bash
--------------

All operations based on pipes require ``bash`` present on hosts operating those pipes. It's usually installed by default on many Linux distributions.

Optional: pv
------------

Rate-limiting transfers while synchronizing is achieved with ``pv`` on the sending hosts.

.. code:: bash

    sudo apt install pv

Optional: nc
------------

Fast, insecure transfers can be performed via ``nc`` (netcat).

.. code:: bash

    sudo apt install netcat

Optional: xz
------------

If compression beyond what ZFS offers is activated, both the sending and receiving hosts during transfers while synchronizing require ``xz`` to be installed.

.. code:: bash

    sudo apt install pxz-utilsv

Optional: SSH
-------------

``ssh`` may be required if there is the intention of accessing zpools on remote machines.

On Debian/Ubuntu-based systems, the client can be installed as follows:

.. code:: bash

    sudo apt install openssh-client

Similarly, the server can be installed as follows:

.. code:: bash

    sudo apt install openssh-server

For details on its configuration, see `help.ubuntu.com`_ and `OpenSSH wiki book`_ as well as the `ssh man page`_ and the `ssh-keygen man page`_, among other places.

.. _help.ubuntu.com: https://help.ubuntu.com/community/SSH
.. _OpenSSH wiki book: https://en.wikibooks.org/wiki/OpenSSH
.. _ssh man page: https://linux.die.net/man/1/ssh
.. _ssh-keygen man page: https://linux.die.net/man/1/ssh-keygen

``abgleich`` generally assumes password-less logins with public keys. ``abgleich`` can change the user on the target system before performing critical operations - therefore root-logins via SSH are not necessary. Systems accessed via an SSH server are ideally running some form of ``sh`` or ``bash``.

User Accounts
-------------

.. warning::

    It is strongly recommended to operate ``abgleich`` with user privileges only.

``abgleich`` relies on the assumption that the ``zfs`` command is in ``PATH`` for regular users and that operations which do not change data such as ``zfs list`` and ``zfs get`` can successfully be performed by the same regular users. For "invasive" operations such as synchronizing two zpools, it is recommended to created dedicated user accounts on all involved machines and to grant them specific rights only:

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

.. warning::

    On Linux, ``zfs allow`` has a known fundamental limitation with regard to operations requiring ``mount`` our ``umount``. From the man page: "Delegations are supported under Linux with the exception of mount, unmount, mountpoint, canmount, rename, and share. These permissions cannot be delegated because the Linux mount(8) command restricts modifications of the global namespace to the root user." A `deeper discussion can be found on Github`_. In this case, the only real option is to perform said operations as root.

Through location strings, ``abgleich`` can be directed to change user with ``sudo`` or ``sudo -u`` respectively before performing certain operations. This change is assumed to work without password. A matching entry in ``/etc/sudoers`` may look as follows:

.. code::

    regular_user ALL=(privileged_user) NOPASSWD: /usr/sbin/zfs

``privileged_user`` may also be ``root`` if mount/umount on Linux is required.

.. _deeper discussion can be found on Github: https://github.com/openzfs/zfs/discussions/10648

Upgrading ``abgleich``
----------------------

Simply re-install the (latest) pre-build binary as described above.

.. note::

	If you are relying on *abgleich*, please notice that it uses **semantic versioning**. Breaking changes are indicated by increasing the second version number, the minor version. Going for example from ``0.0.x`` to ``0.1.y`` or going from ``0.1.x`` to ``0.2.y`` therefore indicates a breaking change.
