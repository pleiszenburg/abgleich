from enum import Enum, auto
from platform import system

from typeguard import typechecked


@typechecked
class Platform(Enum):
    """
    represent platforms abgleich can run on
    """

    linux = auto()
    freebsd = auto()

    if system().lower() == "linux":
        current = linux
        other = freebsd
    elif system().lower() == "freebsd":
        current = freebsd
        other = linux
    else:
        raise ValueError("platform not supported")
