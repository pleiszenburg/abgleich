import re
from abc import ABC, abstractmethod
from typing import Any, Optional, Self

from typeguard import typechecked


@typechecked
class Description(ABC):
    """
    abstract base class for all description classes
    """


@typechecked
class ApoolDescription(Description):
    """
    a single entry from the ls pools output
    columns: alias, route, user, root
    """

    def __init__(self, route: str, root: str, alias: Optional[str] = None, user: Optional[str] = None):
        self._alias = alias
        self._route = route
        self._user = user
        self._root = root

    @property
    def alias(self) -> Optional[str]:
        return self._alias

    @property
    def route(self) -> str:
        return self._route

    @property
    def user(self) -> Optional[str]:
        return self._user

    @property
    def root(self) -> str:
        return self._root


@typechecked
class EntryDescription(Description, ABC):
    """
    abstract base class for tree entry descriptions
    """

    _TYPE_CHARS = dict(
        f = "filesystem",
        v = "volume",
        s = "snapshot",
    )
    _SNAP_CHARS = dict(
        a = "always",
        c = "changed",
        n = "never",
    )

    _PATTERN = None

    @abstractmethod
    def __init__(
        self, host: str,
        path: str,
        root: str,
        type_: str,
        used: Any = None,
        referenced: Any = None,
        compressratio: Any = None,
    ):
        self._host = host
        self._path = path
        self._root = root
        self._type = type_
        self._used = used
        self._referenced = referenced
        self._compressratio = compressratio

    @property
    def host(self) -> str:
        return self._host

    @property
    def path(self) -> str:
        return self._path

    @property
    def root(self) -> str:
        return self._root

    @property
    def type_(self) -> str:
        return self._type

    @property
    def used(self) -> Any:
        return self._used

    @property
    def referenced(self) -> Any:
        return self._referenced

    @property
    def compressratio(self) -> Any:
        return self._compressratio

    @classmethod
    def from_row(cls, row: dict, json: bool) -> Self:
        type_ = row["type"] if json else cls._TYPE_CHARS[row["t"]]
        fields = dict(
            name = row["name"],
            type_ = type_,
            used = row.get("used"),
            referenced = row.get("referenced"),
            compressratio = row.get("compressratio"),
        )
        if type_ == "snapshot":
            return SnapshotDescription(**fields)
        fields["snap"] = row.get("snap") if json else (
            cls._SNAP_CHARS[row["s"]] if row["s"] is not None else None
        )
        return DatasetDescription(**fields)


@typechecked
class DatasetDescription(EntryDescription):
    """
    a single dataset entry from the ls tree output
    """

    _PATTERN = re.compile(r"^(?P<host>[^:]+):(?P<root>[^/]+)(?P<path>/.*)$")

    def __init__(self, name: str, type_: str, snap: str, **kwargs):
        m = self._PATTERN.fullmatch(name)
        if m is None:
            raise ValueError(f"unexpected name: {name!r}")
        super().__init__(
            host = m.group("host"),
            path = m.group("path"),
            root = m.group("root"),
            type_ = type_,
            **kwargs,
        )
        self._snap = snap

    @property
    def snap(self) -> str:
        return self._snap


@typechecked
class SnapshotDescription(EntryDescription):
    """
    a single snapshot entry from the ls tree output
    """

    _PATTERN = re.compile(r"^(?P<host>[^:]+):(?P<root>[^/]+)(?P<path>/[^@]*)@(?P<snapshot>.+)$")

    def __init__(self, name: str, type_: str, **kwargs):
        m = self._PATTERN.fullmatch(name)
        if m is None:
            raise ValueError(f"unexpected name: {name!r}")
        super().__init__(
            host = m.group("host"),
            path = m.group("path"),
            root = m.group("root"),
            type_ = type_,
            **kwargs,
        )
        self._snapshot = m.group("snapshot")

    @property
    def snapshot(self) -> str:
        return self._snapshot
