:github_url:

abgleich
========

**zfs sync tool**

*/ˈapɡlaɪ̯ç/* - German, noun, male: `comparison, replication, alignment`_

.. _comparison, replication, alignment: https://dict.leo.org/englisch-deutsch/abgleich

User's guide
------------

*abgleich* is a simple *ZFS* sync tool. It displays source and target *ZFS* zpool, dataset and snapshot trees. It creates meaningful snapshots only if datasets have actually been changed. It compares a source zpool tree to a target, backup zpool tree. It pushes backups from a source to a target. It cleanes up older snapshots on the source side if they are present on the target side. It runs on a command line and produces nice, user-friendly, human-readable, colorized output. It also includes a GUI.

.. warning::

    This manual describes what makes *abgleich* special and how it runs on top of *ZFS*. It does **NOT** substitute the `OpenZFS documentation`_. Please read the latter first if you have never used ZFS before. Besides the official documentation, an excellent yet dated basic introduction into ZFS is provided in a `series of blog posts`_ by Aaron Toponce.

.. _OpenZFS documentation: https://openzfs.github.io/openzfs-docs/
.. _series of blog posts: https://pthree.org/2012/04/17/install-zfs-on-debian-gnulinux/

.. toctree::
    :maxdepth: 2
    :caption: Introduction

    introduction
    installation
    gettingstarted

.. toctree::
    :maxdepth: 2
    :caption: Reference

    configuration
    cli
    gui
    api

.. toctree::
    :maxdepth: 2
    :caption: Advanced

    bugs
    changes
    support

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
