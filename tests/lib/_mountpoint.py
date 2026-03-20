from abc import ABC, abstractmethod
import os
from typing import Optional

from typeguard import typechecked

from ._command import Command
from ._host import Host


@typechecked
class Mountpoint(ABC):
    """
    base class zpool/dataset mountpoint option
    """

    @abstractmethod
    def __init__(self):
        """
        init
        """

    @staticmethod
    def from_disk(dataset: str, host: Host):
        """
        from option state on disk
        """

        res = Command("zfs", "get", "-Hp", "mountpoint", dataset).with_sudo().on_host(host).run()
        res.assert_exitcode(0)
        _, _, value, source = res.stdout.strip().decode("utf-8").split("\t")

        if source.startswith("inherited"):
            return MntInherit()
        return MntLocal.from_option(value)


class MntInherit(Mountpoint):
    """
    auto-generate mountpoint based on parent path (if parent is mounted)
    """

    def __init__(self):
        """
        init
        """


class MntLocal(Mountpoint):
    """
    do not mount zpool/dataset
    """

    def __init__(self, value: Optional[str] = None):
        """
        init
        """

        self._value = value

    @property
    def value(self) -> Optional[str]:
        """
        value of local mountpoint property
        """

        return self._value

    def to_value_abs(self, root: str):
        """
        join value with root if value is relative, else return value only
        """

        if self._value is None:
            return None
        if os.path.isabs(self._value):
            return self._value
        return os.path.abspath(os.path.join(root, self._value))

    def to_option(self) -> str:
        """
        to option for being set on disk
        """

        return "none" if self._value is None else self._value

    def to_option_abs(self, root: str) -> str:
        """
        to option for being set on disk
        """

        value = self.to_value_abs(root)

        if value is None:
            return "none"
        return value

    @classmethod
    def from_option(cls, value: str):
        """
        from option read from disk
        """

        return cls(None if value == "none" else value)
