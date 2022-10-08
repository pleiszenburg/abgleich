Introduction
============


Why?
----

ZFS is useful in so many ways ... Next to ZFS' reliability, ZFS send/receive is really fast, no matter how many small files or fragments are being dealt with. It can also handle sending/receiving compressed datasets without decompression. Stream / pipe-based approach, easily extensible, a true invitation to write advanced, custom tools.

Searching for a tool of this kind: Quality, reliability (mathematically sound), object orientation / model i.e. extensible (no shell script collection) ... lots of bits and pieces but nothing really good.

Stand-alone application with both CLI and native GUI (no web ui thing)

Specific design goals: Create snapshots only if there are actually changes in a dataset (similar to git commits). Clean snapshot history.

Advanced use-cases beyond backups like syncing multiple workstations (again like git, just scaled up and faster).


A Discussion and Demo of `abgleich` (in German)
-----------------------------------------------

Youtube ...


Alternative ZFS-based Tools
---------------------------

zfs-autosnapshot ...


Noteworthy Alternative Sync and Backup Tools
--------------------------------------------

rsync

