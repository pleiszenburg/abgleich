:github_url:

abgleich
========

**zfs sync tool**

*/ˈapɡlaɪ̯ç/* - German, noun, male: `comparison, replication, alignment`_

.. _comparison, replication, alignment: https://dict.leo.org/englisch-deutsch/abgleich

User's guide
------------

*abgleich* is an opinionated `ZFS`_ management and backup tool, to a certain extend inspired by workflows established by `distributed version control`_ software like ``git``. Think of snapshots as commits. No change, no snapshot, unless you say so explicitly. While branches are allowed, the downside is that classic merges and rebases are technically not feasible on ZFS. Nevertheless, *abgleich* can efficiently transfer ZFS datasets and snapshots from one zpool to another, regardless of the zpools' locations. Push and pull operation is therefore possible, but also transfers between two remote hosts.

.. _ZFS: https://en.wikipedia.org/wiki/ZFS
.. _distributed version control: https://en.wikipedia.org/wiki/Distributed_version_control

.. warning::

    This manual describes what makes *abgleich* special and how it runs on top of *ZFS*. It does **NOT** substitute the `OpenZFS documentation`_. Please read the latter first if you have never used ZFS before. Besides the official documentation, an excellent yet dated basic introduction into ZFS is provided in a `series of blog posts`_ by Aaron Toponce, archived by the Internet Archive.

.. _OpenZFS documentation: https://openzfs.github.io/openzfs-docs/
.. _series of blog posts: https://web.archive.org/web/20230904234829/https://pthree.org/2012/04/17/install-zfs-on-debian-gnulinux/

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
    environment
    performance

.. toctree::
    :maxdepth: 2
    :caption: Advanced

    bugs
    development
    changes
    support

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
