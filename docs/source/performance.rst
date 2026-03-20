.. _performance:

Performance
===========

There are two fundamentally different types of performance tuning:

1) The network is slow and therefore the bottleneck. The more data gets compressed, the better. CPU time is usually not a concern.
2) The network is fast and software becomes the bottleneck, i.e. ZFS and, must likely, SSH effectively limit what can be transferred. CPU time is the main concern while compression might even be an obstacle.

If the network is the bottleneck, the common solution is to compress the transferred data stream while of cause also being conservative in terms of what actually has to be transferred. Although ZFS supports compression, it is usually best to let ZFS decompress the data as part of ``zfs send`` and then pipe it through ``xz`` afterwards with maximum compression applied. On the receiving side, ``xz`` can be used to decompress and ZFS can subsequently re-apply its own compression.

In fast networks, SSH almost always becomes the primary bottleneck. Depending on CPU and fine-tuning, it usually tops out at around 200 to 300 MByte/s or 20 to 30% bandwidth of a 10GBit/s link. If the network can be trusted, it is common to drop SSH for ``zfs send`` and ``zfs receive`` entirely in favour of transferring data with ``netcat``. This approach is known to saturate a 10GBit/s link assuming sufficient read speeds in the sending zpool itself.

.. note::

    Both ``netcat`` and custom stream compression is supported in ``abgleich`` version 0.1 but currently missing from 0.2. It will be re-implemented at a later point in time.

Tuning SSH-based transfers
--------------------------

With the CPU being the bottleneck, the main goal is to reduce CPU load. ``abgleich`` already by default does not decompress ZFS data on ``zfs send``, which eliminates a substantial amount of work. This leaves SSH as the main bottleneck. Two effects are critical:

1) SSH can apply its own compression, which should simply be deactivated.
2) SSH's encryption, which can slow things down well below 100 MByte/s even on modern systems. SSH supports different cyphers with different speeds, some of which are accelerated by `AES-NI`_. Choose a cypher which is supported by both the client and the server which uses this feature. This may increase throughput to anywhere from roughly 200 to 300 MByte/s as far as SSH is concerned.

A sample SSH client configuration may look as follows:

.. code:: text

    Host somealias
        Hostname example.com
        Port 2022
        User username
        Compression no
        PubkeyAuthentication yes
        IdentityFile ~/.ssh/some.key
        Ciphers aes256-gcm@openssh.com

.. _AES-NI: https://en.wikipedia.org/wiki/AES_instruction_set

