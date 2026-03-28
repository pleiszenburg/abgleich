# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# IMPORT
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import os
from tomllib import loads


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ROUTINES
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


def parse_version(code: str) -> str:

    data = loads(code)
    return data["package"]["version"]


def get_version() -> str:

    path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "abgleich-lib",
        "Cargo.toml",
    )

    with open(path, "r", encoding="utf-8") as f:
        version = parse_version(f.read())

    return version
