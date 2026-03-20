from typing import Any

from typeguard import typechecked

from ._command import Command
from . import _dataset
from ._host import Host


@typechecked
class Snapshot:
    """
    zfs dataset
    """

    def __init__(self, name: str):
        """
        init
        """

        self._name = name

        self._parent = None

    def __repr__(self) -> str:
        """
        interactive representation
        """

        return f"<Snapshot name={self._name:s}>"

    def __eq__(self, other: Any) -> bool:
        """
        eq op
        """

        if not isinstance(other, type(self)):
            return NotImplemented

        return self._name == other.name

    def __hash__(self) -> int:
        """
        hash op
        """

        return hash(self._name)

    @property
    def name(self) -> str:
        """
        name of snapshot
        """

        return self._name

    @property
    def full_name(self) -> str:
        """
        get full zfs name of snapshot
        """

        if self._parent is None:
            raise ValueError("snapshot is currently not on disk")

        return f"{self._parent.full_name:s}@{self._name:s}"

    @property
    def parent(self) -> "_dataset.Dataset":
        """
        parent
        """

        return self._parent

    @parent.setter
    def parent(self, value: "_dataset.Dataset"):
        """
        parent
        """

        self._parent = value

    def copy(self):
        """
        full copy
        """

        return type(self)(
            name = self._name,
        )

    def create(self, parent: "_dataset.Dataset", host: Host):
        """
        create snapshot within dataset
        """

        self._parent = parent

        res = Command(
            "zfs",
            "snapshot",
            self.full_name,
        ).with_sudo().on_host(host).run()
        res.assert_exitcode(0)

    def destroy(self, host: Host):
        """
        destroy snapshot within dataset
        """

        res = Command(
            "zfs",
            "destroy",
            self.full_name,
        ).with_sudo().on_host(host).run()
        res.assert_exitcode(0)

    def reload(self, host: Host):
        """
        reload snapshot
        """

        # currently nothing to do here

    @classmethod
    def from_name(cls, name: str, parent: "_dataset.Dataset", host: Host):
        """
        from name
        """

        snapshot = cls(
            name = name,
        )
        snapshot.parent = parent
        return snapshot
