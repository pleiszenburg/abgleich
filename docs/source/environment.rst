.. _environment:

Environment Variables
=====================

Basic behaviour:

- ``ABGLEICH_CONFIG``: Overrides configuration file detection, allowing to provide a specific path instead.
- ``ABGLEICH_LOGLEVEL``: Allows to set log-level as integer, matching those of the `Python standard library`_. Defaults to ``30`` (``WARN``).

Overrides for custom ZFS properties:

- ``ABGLEICH_DIFF``: Check diff of dataset for determining if a snapshot is required. Overrides ``abgleich:diff`` properties.
- ``ABGLEICH_FORMAT``: Format for name of new snapshots. Overrides ``abgleich:format`` properties.
- ``ABGLEICH_OVERLAP``: Number of overlapping snapshots on source and target. Overrides ``abgleich:overlap`` properties.
- ``ABGLEICH_SNAP``: Controls overall snapshot behaviour. Overrides ``abgleich:snap`` properties.
- ``ABGLEICH_SYNC``: Controls overall sync behaviour. Overrides ``abgleich:sync`` properties.
- ``ABGLEICH_THRESHOLD``: Only if changes are smaller than this number of bytes, a dataset will be diffed to look for changes. Overrides ``abgleich:threshold`` properties.

.. _Python standard library: https://docs.python.org/3/library/logging.html#logging-levels
