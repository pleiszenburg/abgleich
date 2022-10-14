Introduction
============


Why another tool for performing ZFS-related tasks?
--------------------------------------------------

ZFS is useful in many different ways. It does not restrict the user to a specific workflow. Instead, it provides an impressive collection of basic tools, commands, APIs and "building blocks" for doing just about anything imaginable when it comes to storage while being actually incredible reliable. Next to ZFS' reliability, ZFS's ``send`` & ``receive`` commands are really fast operations, no matter how many small files or fragments are that being dealt with. The mentioned commands can also handle sending and receiving compressed datasets without extra decompression/compression steps which are rather common in other, similar tools. ZFS' stream or pipe-based approach, tightly integrating into Unix-like environments, is easily extensible and a true invitation for writing advanced, custom tools on top.

In stark contrast, while searching for a management, replication and backup tool for ZFS around 2016, one gap stood out in this part of the ecosystem: A lack of quality, limited reliability especially in a mathematical sense and basically no meaningful form of code structure, e.g. object orientation. Many tools are written in shell languages such as e.g. ``bash`` or, even worse, in languages like ``PHP``. Virtually all of them come without proper test suites. Most of them fall apart when using them in an "unusual manner" just a tiny little bit. All of them make implicit assumptions about the structure and usage of zpools and/or surrounding computer networks, which, if not followed precisely to the letter, can cause data loss in worst-case-scenarios. None of the tools make an effort to model zpools or their workflows in any form, making them extra hard to debug or understand and ultimately impossible to extend. As a less problematic but still annoying side note, most existing tools are lacking any form of proper user interface. The CLI interfaces commonly found require a ton of experience and are not forgiving mistakes. Native GUIs are virtually non-existing. Web UIs intended for system administrators and narrow use cases are usually the only half-decent user interfaces available.


Design goals
------------

The fundamental idea is to **synchronize portions of two zpools** on potentially, but not necessarily, two different physical computers. This may be for backups but also for moving "projects" or virtual machines around between different workstations or servers.

The overall approach should be as robust as possible, allowing for fine-grained tests, easy maintenance and good extensibility. Under no circumstances, even if misconfigured, should the tool allow data loss to occur, ideally making it just as reliable as the ZFS filesystem underneath. It should be possible to mathematically proof the latter.

Two of the requirements that led to ``abgleich`` being developed was as-fast-as-possible transfers while also allowing to optimize for the data volume being transferred during backups in low-bandwidth-environments.

By default, ``abgleich`` generates a sequence of atomic transactions which are presented to the user for confirmation before acting on them. In this regard, it behaves rather similar to partitioning tools such as *parted* or *GParted*.

While the tool can be used on headless servers, it is explicitly also aiming at laptops, desktop computers and workstations running on ZFS. Proper command line and graphical user interfaces for "end users" are therefore required. A single API is driving the different types of user interfaces.

ZFS' ability to create and clone snapshots allows to mimic workflows similar to what is possible with ``git``. Just like ``git`` "commits", the idea is to only create snapshots if a dataset/volume actually contains changes. In the ZFS world, this is a rather unusual design choice as it is common practise to generate snapshot in fixed time intervals regardless of changes in the dataset/volume. ``abgleich`` implements special logic to safely and quickly determine if a dataset/volume contains "uncommitted" changes.

With regards to similarities to ``git``, ``abgleich`` aims to provide the ability to synchronize "projects" (datasets/volumes) across multiple computers in addition to providing backup functionality. Projects can be "moved" or "cloned" from one machine to the next, allowing a user to always work on them efficiently and locally. Besides, synchronization operations can happen both in a pull and a push configuration.


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

It has been attempted to build similar tools on top of `BTRFS`_, which did not take of as much as initially expected despite being seen as a better or purer version of ZFS, i.e. less licensing issues. Noteworthy examples include `btrfs-sxbackup`_ and `btrbk`_.

.. _BTRFS: https://btrfs.wiki.kernel.org/index.php/Main_Page
.. _btrfs-sxbackup: https://github.com/masc3d/btrfs-sxbackup
.. _btrbk: https://github.com/digint/btrbk

Besides, there is a rather mature family of similar tools based on `rsync`_, which primarely suffer from the significant performance overhead of having to go through all of the filesystem's layers where ZFS-based tools in comparison can operate on a rather low block-level.

.. _rsync: https://en.wikipedia.org/wiki/Rsync

Another noteworthy example offering similar capabilities but operating on top of the filesystem as well is `Borg`_.

.. _Borg: https://www.borgbackup.org/

Although ``git`` itself is not intended to manage large binary files or simply very high numbers of files at once, it can be extended with plugins such as `git-lfs`_ to provide capabilities very similar to ``abgleich``. Unfortunately, any ``git``-based approach will suffer from filesystem-overhead just like ``rsync``, next to other issues. Other approaches based on ``git`` have been developed by Microsoft for dealing with very large mono-repos. Examples include `VFS for Git`_ (first generation, abandoned), `Scalar`_ (second generation, abandoned) and `microsoft/git`_ (third and current generation).

.. _git-lfs: https://git-lfs.github.com/
.. _VFS for Git: https://github.com/microsoft/VFSForGit
.. _Scalar: https://github.com/microsoft/scalar
.. _microsoft/git: https://github.com/microsoft/git
