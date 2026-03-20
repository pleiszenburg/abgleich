from enum import Enum, auto

from typeguard import typechecked

from ._platform import Platform


@typechecked
class Host(Enum):
    """
    represents all VMs in test setup
    """

    localhost = auto()

    current_a = localhost
    current_b = auto()
    other_a = auto()
    other_b = auto()

    def to_config_name(self) -> "str":
        """
        translate to name as used in test configuration
        """

        return self.name if self.name != "localhost" else "current_a"

    def to_host_name(self) -> "str":
        """
        translate to host name for ssh etc
        """

        if self is Host.localhost:
            return "localhost"

        if Platform.current is Platform.linux:
            if self is Host.current_b:
                return "linux-b"
            if self is Host.other_a:
                return "freebsd-a"
            if self is Host.other_b:
                return "freebsd-b"
            raise ValueError("should never happen")

        if Platform.current is Platform.freebsd:
            if self is Host.current_b:
                return "freebsd-b"
            if self is Host.other_a:
                return "linux-a"
            if self is Host.other_b:
                return "linux-b"
            raise ValueError("should never happen")

        raise ValueError("should never happen")

    @classmethod
    def from_config_name(cls, name: str):
        """
        from node name as used in test configuration
        """

        return getattr(cls, name)
