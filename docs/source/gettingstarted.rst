.. _gettingstarted:

Getting Started
===============

.. note::

    This chapter assumes that your systems meet all required prerequisites and you have ``abgleich`` installed. For details see :ref:`chapter on prerequisites and installation <installation>`.


Workflow
--------

The fundamental idea is to **synchronize portions of two zpools** on potentially, but not necessarily, two different physical computers. The first one is called the ``source``, the second one is called the ``target``. A **typical workflow has three steps**:

1) **snap**: Creating snapshots on the ``source`` side for datasets/volumes containing changes since last snapshot.
2) **backup**: Copying those snapshots currently not present on the ``target`` from the ``source`` to the ``target``.
3) **cleanup**: Removing all but the last ``n`` snapshots per dataset/volume on the ``source`` side. Optionally also remove all but the last ``m`` snapshots from the ``target`` side which do not overlap with snapshots on the ``source`` side.


Example ZFS deployment
----------------------

For introductory purposes, two machines are assumed to exist: The ``sourcebox`` and the ``targetbox``. ``abgleich`` runs on the ``sourcebox``. Each machine has a zpool, conveniently named ``sourcepool`` and ``targetpool``. The ``sourcebox`` might be a workstation or some kid of a server holding data for e.g. virtual machines. This is where "data is created/changed". The target might be a hot spare machine or simply a remote backup machine. This is where data is synchronized to.

Let's further assume that everything within the dataset ``sourcepool/data`` and below should be synced with the dataset ``targetpool/sourcebackup/data`` and below. ``data`` is the "prefix" for the source zpool, ``sourcebackup/data`` is the corresponding "prefix" for the target zpool. For ``abgleich`` to work, ``sourcepool/data`` and ``targetpool/sourcebackup`` must exist. ``targetpool/sourcebackup/data`` can exist, but it does not have to. The latter can be created by ``abgleich``.

.. warning::

    It is highly recommended to set the mountpoint of ``targetpool/sourcebackup`` to ``none`` before running ``abgleich`` for the first time. This avoids unintended changes to the descendants of ``targetpool/sourcebackup``.


Initial configuration
---------------------

Before a typical workflow can be performed, ``abgleich`` must be configured through a :ref:`configuration file <configuration>`. The :ref:`CLI <cli>` provides a dedicated command-line wizard for creating one, ``abgleich init filename.yaml``, but it can of cause also be written by hand.

For the described example deployment, a minimal configuration file perhaps named ``config.yaml`` might look as follows:

.. code::yaml

    source:
        prefix: data
        zpool: sourcepool
    target:
        host: targethost
        prefix: sourcebackup/data
        zpool: targetzpool

Snap
----

Now its time for the first step of the workflow, creating snapshots on the ``source`` side, i.e. for ``sourcepool/data`` and below. This is performed by ``abgleich snap config.yaml``.

- TODO image

By default, ``abgleich`` only creates snapshots if datasets/volumes actually contain changes. However, this behaviour can be adjusted.

Backup
------

After creating snapshots on the source side, snapshots are copied from the ``source`` side over to the ``target`` side in the second step by invoking ``abgleich backup config.yaml``.

- TODO image

In this step, ``sourcepool/data`` and ``targetpool/sourcebackup/data`` are recursively compared to figure out what needs to be copied. Perhaps multiple new snapshots have been created for a certain dataset. Or none at all.

Cleanup
-------


- TODO image

