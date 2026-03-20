.. _development:

Development
===========

Setup for Building
------------------

`just`_ >= 1.46 is used as a command runner, also see `just installation instruction`_ for installation instructions. Some Linux distributions and FreeBSD tend to ship very outdated versions of ``just``.

Next, obtain Rust, see `install Rust`_ for further details.

The project uses `cross`_ for building, which requires a container runtime, either `docker`_ or `podman`_. Once installed, ``just build {target}`` and ``just release {target}`` can be used for debug or release builds.

`upx`_ is required for compressed Linux binaries.

.. _just: https://github.com/casey/just
.. _just installation instruction: https://github.com/casey/just?tab=readme-ov-file#installation
.. _install Rust: https://www.rust-lang.org/tools/install
.. _cross: https://github.com/cross-rs/cross
.. _docker: https://docs.docker.com/
.. _podman: https://podman.io/docs
.. _upx: https://github.com/upx/upx

Local Building on Linux
^^^^^^^^^^^^^^^^^^^^^^^

Alternatively, one can also build locally without using ``cross``. Production releases on Linux link against `musl`_. For this purpose, a special compiler target must be installed:

.. code:: bash

    rustup target add x86_64-unknown-linux-musl

A matching x86_64 GCC wrapper for linking against `musl` must be installed in addition via:

.. code:: bash

    sudo apt install musl-tools

.. _musl: https://en.wikipedia.org/wiki/Musl

Local Building on FreeBSD
^^^^^^^^^^^^^^^^^^^^^^^^^

No extra requirements.

Setup for Testing
-----------------

Tests run in isolated virtual machines managed by `vagrant` for both Linux and FreeBSD tests. On Debian/Ubuntu/Mint systems:

.. code:: bash

    sudo apt install vagrant virtualbox`

Virtual machines with Linux and FreeBSD guests can then be provisioned by running:

.. code:: bash

    just setup linux
    just setup freebsd

This will create 4 VMs, two nodes running Linux plus two nodes running FreeBSD.

VMs can be controlled through a number of convenience wrappers: ``just reset {platform}`` (halt, reset to initial state, boot) and ``just halt {platform}`` (simply shut down) are probably the most important ones. ``{platform}`` can be either ``linux`` or ``freebsd``.

Setup for Checking Feature Flags
--------------------------------

Unexpected combinations of feature flags are known to break applications if not treated carefully. This project uses `cargo-hack`_ to check if all possible / allowed feature permutations actually result in compiled code. Once installed, it can be triggered as follows:

.. code:: bash

    just test-features

.. _cargo-hack: https://github.com/taiki-e/cargo-hack

Setup for Detailed Linting
--------------------------

This project aspires to pass tests by `clippy`_. Once installed, it can be triggered as follows:

.. code:: bash

    just clippy

.. _clippy: https://github.com/rust-lang/rust-clippy

Setup for Linting the Test Suite
--------------------------------

Python should be >= 3.12. For system-Python on recent Debian/Ubuntu/Mint system, the following should do:

.. code:: bash

    sudo apt install python3 python3-dev python3-venv python3-pip

Set up the Python portion of the testing tools in a dedicated Python virtual environment:

.. code:: bash

    python3 -m venv env
    source env/bin/activate
    pip install -vU pip setuptools
    pip install -vr tests/requirements.txt

Alternatively, ``conda`` can also be used, see `miniforge`_.

.. _miniforge: https://github.com/conda-forge/miniforge

Building the Documentation
--------------------------

Assuming the previously created Python virtual environment, the required dependencies can be installed as follows:

.. code:: bash

    pip install -vr docs/requirements.txt

Then, the documentation can be build as follows:

.. code:: bash

    just clean-docs
    just docs-build

The built docs are located in ``docs/build``.

Development Commands
--------------------

There two types of tests. First, a test suite using ``pytest``, testing through the CLI of ``abgleich``. This is where most tests happen, done through tests on virtual machines. Second, there is tests contained in the Rust-code tested through ``cargo``, and feature-build tests.

Testing the CLI
^^^^^^^^^^^^^^^

Clean up stuff:

.. code:: bash

    just clean-build  # all build relicts
    just reset linux  # reset Linux VMs to known-good state
    just reset freebsd  # reset FreeBSD VMs to known-good state

Build specific debug binaries:

.. code:: bash

    just build x86_64-unknown-linux-musl
    just build x86_64-unknown-linux-gnu
    just build x86_64-unknown-freebsd

Build specific release binaries:

.. code:: bash

    just release x86_64-unknown-linux-musl
    just release x86_64-unknown-linux-gnu
    just release x86_64-unknown-freebsd

Run all tests against debug builds:

.. code:: bash

    just test linux
    just test freebsd

Run specific tests against debug builds, see `pytest -k`_ for what is a valid expression:

.. code:: bash

    just debug {platform} {expression}

.. _pytest -k: https://docs.pytest.org/en/stable/how-to/usage.html#specifying-which-tests-to-run

Testing Internals and Features
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Test internal tests within the Rust code:

.. code:: bash

    just test-internal

Test feature permutations:

.. code:: bash

    just test-features

Environment Variables for Testing
---------------------------------

- ``ABGLEICH_TEST_LOGTODISK``: Set to ``1`` for writing test logs to disk
- ``ABGLEICH_TEST_RELEASE``: Set to ``1`` for testing release builds instead of debug builds
- ``ABGLEICH_TEST_TARGET``: Test specific build targets, interesting primarily on Linux with possible values being ``x86_64-unknown-linux-musl`` (equivalent of ``default``) or ``x86_64-unknown-linux-gnu``
- ``ABGLEICH_TEST_VERBOSE``: Set to ``1`` for much more verbosity during testing

Environment variables starting with ``RUST`` such as ``RUST_BACKTRACE`` are passed through.
