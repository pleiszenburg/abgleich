.. _cli:

.. DO NOT MANUALLY EDIT THIS FILE! IT IS OVERWRITTEN FOR EACH BUILD BY `update_cli.py`.

CLI
===

The command line interface (CLI).

``abgleich``
------------

.. code:: text

    abgleich, zfs sync tool
    
    Usage: abgleich <COMMAND>
    
    Commands:
      free     remove old snapshots from source datasets, freeing up space, while snapshots remain on target
      ls       show list of apools/zpools and/or a list/tree of datasets
      snap     create snapshots of changed datasets for backups
      sync     sync a dataset tree into another
      version  show version
      help     Print this message or the help of the given subcommand(s)
    
    Options:
      -h, --help     Print help
      -V, --version  Print version

``abgleich free``
-----------------

.. code:: text

    remove old snapshots from source datasets, freeing up space, while snapshots remain on target
    
    Usage: abgleich free [OPTIONS] <SOURCE> <TARGET>
    
    Arguments:
      <SOURCE>  alias or [route:][user%]root
      <TARGET>  alias or [route:][user%]root
    
    Options:
      -j, --json   output as json
      -y, --yes    answer all questions with yes
      -f, --force  attempt all transactions even if some fail; exit non-zero if any failed
      -h, --help   Print help

``abgleich ls``
---------------

.. code:: text

    show list of apools/zpools and/or a list/tree of datasets
    
    Usage: abgleich ls [OPTIONS] [LOCATION]
    
    Arguments:
      [LOCATION]  void, alias or [route:][user%]root
    
    Options:
      -j, --json  output as json
      -h, --help  Print help

``abgleich snap``
-----------------

.. code:: text

    create snapshots of changed datasets for backups
    
    Usage: abgleich snap [OPTIONS] <LOCATION>
    
    Arguments:
      <LOCATION>  alias or [route:][user%]root
    
    Options:
      -j, --json   output as json
      -y, --yes    answer all questions with yes
      -f, --force  attempt all transactions even if some fail; exit non-zero if any failed
      -h, --help   Print help

``abgleich sync``
-----------------

.. code:: text

    sync a dataset tree into another
    
    Usage: abgleich sync [OPTIONS] <SOURCE> <TARGET>
    
    Arguments:
      <SOURCE>  alias or [route:][user%]root
      <TARGET>  alias or [route:][user%]root
    
    Options:
      -j, --json                     output as json
      -y, --yes                      answer all questions with yes
      -d, --direct                   run transfer pipe on common entry host, where bash is required
      -f, --force                    attempt all transactions even if some fail; exit non-zero if any failed
      -r, --rate-limit <RATE_LIMIT>  limit transfer bandwidth on the sending host via pv (e.g. 10m, 500k, 1g)
      -x, --compress [<COMPRESS>]    xz compression level (0–9); suppresses `zfs send -c` because sending pre-compressed blocks would reduce xz efficiency.  Omit the flag entirely to disable xz (uses `zfs send -c` instead).  Pass `-x` without a value for the default level 5.  Pass `-x N` or `-x=N` for a specific level (0 = fastest, 9 = best compression)
          --insecure <INSECURE>      bypass SSH for data transfer: receiver uses `nc -l PORT | zfs receive`, sender uses `zfs send | nc HOST PORT`; format: host:port (mutually exclusive with --direct)
      -h, --help                     Print help

