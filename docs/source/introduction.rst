Introduction
============


Why another tool for performing ZFS-related tasks?
--------------------------------------------------

ZFS is useful in many different ways. It does not restrict the user to a specific workflow. Instead, it provides an impressive collection of basic tools, commands, APIs and "building blocks" for doing just about anything imaginable when it comes to storage while being actually incredible reliable. Next to ZFS' reliability, ZFS's ``send`` & ``receive`` commands are really fast operations, no matter how many small files or fragments are being dealt with. They can also handle sending and receiving compressed datasets without decompression. The stream or pipe-based approach is easily extensible and a true invitation for writing advanced, custom tools on top.

In stark contrast, while searching for a management, replication and backup tool for ZFS around 2016, one gap stood out in this part of the ecosystem: A lack of quality, limited reliability especially in a mathematical sense and basically no meaningful form of code structure, e.g. object orientation. Many tools are written in shell languages such as e.g. ``bash`` or, even worse, in languages like ``PHP``. Virtually all of them come without proper test suites. Most of them fall apart when using them in an "unusual manner" just a tiny little bit. All of them make implicit assumptions about the structure and usage of zpools, which, if not followed precisely to the letter, can cause data loss. None of the tools make an effort to model in zpools or their workflows in any form, making them extra hard to debug or understand and ultimately impossible to extend. As a less problematic but still annoying side note, most existing tools are lacking any form of proper user interface. The CLI interfaces require a ton of experience and do not forgive mistakes. Native GUIs are virtually non-existing. Web UIs intended for system administrators and narrow use cases are usually the only user interfaces available.


``abgleich``'s design goals
---------------------------

The overall approach should be as robust as possible, allowing for fine-grained tests, easy maintenance and good extensibility. Under no circumstances, even if misconfigured, should the tool allow data loss to occur, ideally making it just as reliable as the ZFS filesystem underneath. It should be possible to mathematically proof the latter.

While the tool can be used on headless servers, it is explicitly also aiming at laptops, desktop computers and workstations running on ZFS. Proper command line and graphical interfaces for end users are therefore required. A single API is driving the different types of user interfaces.

ZFS ability to create and clone snapshots allows to mimic workflows similar to what is possible with ``git``. Similar to ``git`` "commits", the idea is to only create snapshots if a dataset/volume actually contains changes. In the ZFS world, this is a rather unusual design choice as it is common practise to generate snapshot in fixed time intervals regardless of changes in the dataset/volume. ``abgleich`` implements special logic to safely and quickly determine if a dataset/volume contains "uncommitted" changes.

With regards to similarities to ``git``, ``abgleich`` aims to provide the ability to synchronize "projects" (datasets/volumes) across multiple computers in addition to providing backup functionality. Projects can be "moved" or "cloned" from one machine to the next, allowing a user to always work on them efficiently and locally. Besides, synchronization operations can happen both in a pull and a push configuration.

Basic workflow
--------------

The fundamental idea is to **synchronize portions of two zpools** on potentially, but not necessarily, two different physical computers. The first one is called the ``source``, the second one is called the ``target``. A **typical workflow has three steps**:

1) **snap**: Creating snapshots on the ``source`` side for datasets/volumes containing changes since last snapshot.
2) **backup**: Copying those snapshots currently not present on the ``target`` from the ``source`` to the ``target``.
3) **cleanup**: Removing all but the last ``n`` snapshots per dataset/volume on the ``source`` side. Optionally also remove all but the last ``m`` snapshots from the ``target`` side which do not overlap with snapshots on the ``source`` side.

Video: Discussion and demo of `abgleich` (in German)
----------------------------------------------------

A discussion and "live" demo of ``abgleich`` (in German) can be found `here`_.

.. _here: https://www.youtube.com/watch?v=BjZJmoHnK3Q

Alternative ZFS-based Tools
---------------------------

The one and only, the classic, the bash-nightmare: `zfs-auto-snapshot`_.

.. _zfs-auto-snapshot: https://github.com/zfsonlinux/zfs-auto-snapshot


Noteworthy alternative sync and backup tools
--------------------------------------------

It has been attempted to build similar tools on top of `BTRFS`_, which, as of writing, did not take of as much as initially expected. Noteworthy examples include `btrfs-sxbackup`_ and `btrbk`_.

.. _BTRFS: https://btrfs.wiki.kernel.org/index.php/Main_Page
.. _btrfs-sxbackup: https://github.com/masc3d/btrfs-sxbackup
.. _btrbk: https://github.com/digint/btrbk

Besides, there is a rather mature family of similar tools based on `rsync`_, which (only) suffer from the significant performance overhead of having to go through all of the filesystem's layers where ZFS-based tools in comparison can operate on a rather low block-level.

.. _rsync: https://en.wikipedia.org/wiki/Rsync

Although ``git`` itself is not intended to manage large binary files or simply very high numbers of files at once, it can be extended with plugins such as `git-lfs`_ to provide capabilities very similar to ``abgleich``. Unfortunately, any ``git``-based approach will suffer from filesystem-overhead just like ``rsync``, next to other issues.

.. _git-lfs: https://git-lfs.github.com/
