.. _gettingstarted:

Getting Started
===============

.. note::

    This chapter assumes that your systems meet all required prerequisites and you have ``abgleich`` installed. For details see :ref:`chapter on prerequisites and installation <installation>`.


Workflow
--------

The fundamental idea is to **synchronize portions of two zpools** on potentially, but not necessarily, two different physical computers. The first one is called the ``source``, the second one is called the ``target``. A **typical workflow has three steps**:

1) **snap**: Creating snapshots on the ``source`` side for datasets/volumes containing changes since last snapshot.
2) **sync**: Copying those snapshots currently not present on the ``target`` from the ``source`` to the ``target``.
3) **free**: Removing all but the last ``n`` snapshots per dataset/volume on the ``source`` side.


Example ZFS deployment
----------------------

Two machines are assumed to exist: The ``sourcebox`` and the ``targetbox``. ``abgleich`` runs on the ``sourcebox``. Each machine has a zpool, conveniently named ``sourcepool`` and ``targetpool``. The ``sourcebox`` might be a workstation or some kid of a server holding data for e.g. virtual machines. This is where "data is created/changed". The target might be a hot spare machine or simply a remote backup machine. This is where data is synchronized to. Everything below the dataset ``sourcepool`` should be synced below the dataset ``targetpool/sourcebackup``.

The setup on ``sourcebox`` might look as follows:

.. code::

    NAME                                                 USED  AVAIL     REFER  MOUNTPOINT
    sourcepool                                          35.5G  95.4G      112K  /home
    sourcepool/user_a                                   1.09M  95.4G      532K  /home/user_a
    sourcepool/user_b                                   35.5G  95.4G     13.8G  /home/user_b
    sourcepool/user_b/CACHE                             8.82G  95.4G     8.82G  /home/user_b/.cache
    sourcepool/user_b/DESKTOP                            2.7G  95.4G      2.7G  /home/user_b/Desktop
    sourcepool/user_b/SSH                              120.7K  95.4G      5.2M  /home/user_b/.ssh

The setup on ``targetbox`` might look as follows:

.. code::

    NAME                                                 USED   AVAIL     REFER  MOUNTPOINT
    targetpool                                            64k  570.1G      173K  /backups


Preparation
-----------

For simplicity, this introduction assumes that user ``root`` is used to perform ZFS operations. While ``abgleich`` is supposed to run as a regular user, it can delegate operations via ``sudo`` or ``sudo -u user`` assuming that this does not require a passsword. The simple-most, though not the most secure option on both source and target boxes is to edit ``/etc/sudoers`` and add a line as follows:

.. code::

    myusername ALL=root NOPASSWD: /usr/sbin/zfs

This allows the user ``myusername`` to run ``zfs`` without password via ``sudo``.

The zpool is used to back the ``/home`` directory. Snapshots or backups of ``/home`` itself are not required, but basically almost everything below. While ``user_a`` simply sits on a single dataset, ``user_b`` has a more fine-grained structure. The ``.cache`` is meaningless and is not supposed to be included in backups. On the other hand, ``.ssh`` is critical and always requires snaphots and backups, regardless of changes. The rest should only receive snapshots and backups if there actually are changes.

On the source box, ``abgleich`` needs to be configured accordingly:

.. code:: bash

    sudo zfs set abgleich:snap=never sourcepool/user_b/CACHE  # no snapshots
    sudo zfs set abgleich:sync=off sourcepool/user_b/CACHE  # no sync, no free
    sudo zfs set abgleich:snap=always sourcepool/user_b/SSH

On the target box, the stage needs to be prepared:

.. code:: bash

    sudo zfs create -o mountpoint=none targetpool/sourcepool

Setting the mountpoint to ``none`` is a convenient choice for a backup as it is not meant to be modified and it avoids mount-permission problems with non-root users on Linux.


Backup Cycle
------------

A full cycle may now look as follows:

.. code:: bash

    abgleich snap root%sourcepool/
    abgleich sync root%sourcepool/ targetbox:root%targetpool/sourcepool/
    abgleich free root%sourcepool/ targetbox:root%targetpool/sourcepool/

The tailing slash, ``/``, indicates that ``abgleich`` should work on datasets below a given dataset, but not on the dataset itself.

The cycle can be repeated as many times as required.
