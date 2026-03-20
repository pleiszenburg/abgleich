# top-level just recipes
# ---------------------------------------------------------------------------
# Import into project root justfile with:
#
#     import 'vagrant/top-level.just'
#
# Requires just ≥ 1.18.  The file can also be copied and customised directly
# if per-project modifications are needed or an older just version is in use.
#
# source_directory() resolves to the vagrant/ directory regardless of where
# the importing justfile lives, so no path adjustments are needed.
# ---------------------------------------------------------------------------

# Generate the shared Ed25519 keypair used by all VMs (skips if already present)
generate-keys:
    cd {{ source_directory() }}/keys && just generate-keys

# Tear down VMs for one platform
clean-vm platform=("linux" / "freebsd"):
    cd {{ source_directory() / platform }} && just clean

# Halt VMs for one platform gracefully
halt platform=("linux" / "freebsd"):
    cd {{ source_directory() / platform }} && just halt

# Run the test suite with pytest directly on the host (no VMs required)
pytest:
    #!/usr/bin/env bash
    pytest -r a -s

pytest-debug expression:
    #!/usr/bin/env bash
    pytest -r a -s -k {{expression}}

# First-time setup: generate shared keys then create VMs
setup platform=("linux" / "freebsd"): generate-keys
    cd {{ source_directory() / platform }} && just setup

# Restore VMs to the clean snapshot and wait for SSH
reset platform=("linux" / "freebsd"):
    cd {{ source_directory() / platform }} && just reset

# Run the test suite on the primary VM (VMs assumed running)
test platform=("linux" / "freebsd"):
    #!/usr/bin/env bash
    for var in $(compgen -v ABGLEICH) $(compgen -v RUST); do
        export "$var"
    done
    cd {{ source_directory() / platform }} && just test

# Selectively run tests by filter expression
debug platform expression:
    #!/usr/bin/env bash
    for var in $(compgen -v ABGLEICH) $(compgen -v RUST); do
        export "$var"
    done
    cd {{ source_directory() / platform }} && just debug {{expression}}

# Pass any recipe through to a platform's vagrant justfile
vm platform *args:
    cd {{ source_directory() / platform }} && just {{args}}
