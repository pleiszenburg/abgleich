.. _environment:

Environment Variables
=====================

Basic behaviour:

- ``ABGLEICH_CONFIG``: Overrides configuration file detection, allowing to provide a specific path instead.
- ``ABGLEICH_LOGLEVEL``: Allows to set log-level as integer, matching those of the `Python standard library`_. Defaults to ``30`` (``WARN``).
- ``ABGLEICH_FULLFORCE``: Danger territory. If the ``-f`` / ``--force`` option is used on any subcommand, by default, only subprocesses exiting with a non-zero exit code or those terminated by signals are ignored, i.e. force is applied where it is more or less safe(-ish) to do. However, should a more fundamental error occur such as failing to spawn a subprocess in the first place, decoding issues in its output or anything related to attaching to standard streams, ``abgleich`` will still stop running transactions. If those errors are also supposed to be ignored, **in addition** to using the ``-f`` option, this environment variable can be set to ``1``. Defaults to ``0`` (not active).

Overrides for custom ZFS properties:

- ``ABGLEICH_DIFF``: Check diff of dataset for determining if a snapshot is required. Overrides ``abgleich:diff`` properties.
- ``ABGLEICH_FORMAT``: Format for name of new snapshots. Overrides ``abgleich:format`` properties.
- ``ABGLEICH_OVERLAP``: Number of overlapping snapshots on source and target. Overrides ``abgleich:overlap`` properties.
- ``ABGLEICH_SNAP``: Controls overall snapshot behaviour. Overrides ``abgleich:snap`` properties.
- ``ABGLEICH_SYNC``: Controls overall sync behaviour. Overrides ``abgleich:sync`` properties.
- ``ABGLEICH_THRESHOLD``: Only if changes are smaller than this number of bytes, a dataset will be diffed to look for changes. Overrides ``abgleich:threshold`` properties.

.. _Python standard library: https://docs.python.org/3/library/logging.html#logging-levels
