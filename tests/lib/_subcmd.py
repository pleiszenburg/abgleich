from enum import Enum, auto


class Subcmd(Enum):
    """
    represents all sub commands
    """

    none = auto()

    free = auto()
    ls = auto()
    snap = auto()
    sync = auto()

    version = auto()

    @classmethod
    def all(cls):
        """
        inventory of all sub commands available
        """

        return (item for item in cls)

    def to_cli(self):
        """
        to string as used on CLI
        """

        return self.name.replace("_", "-")
