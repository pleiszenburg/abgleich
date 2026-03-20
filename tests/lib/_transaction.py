import re
from abc import ABC, abstractmethod
from typing import Self

from typeguard import typechecked


class Transaction(ABC):
    """
    abstract base class for all transactions
    """

    _ALL: list[Self] = []

    _PREFIX = None
    _PATTERN = None

    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        Transaction._ALL.append(cls)

    @abstractmethod
    def __init__(self, command: str):
        self._command = command

    @property
    def command(self) -> str:
        return self._command

    @classmethod
    @abstractmethod
    def matches(cls, description: str):
        raise NotImplementedError

    @classmethod
    def from_fields(cls, description: str, command: str) -> Self:
        """
        dispatch a description string to the matching transaction class
        """

        matched = [cls for cls in cls._ALL if cls.matches(description)]
        if len(matched) == 1:
            return matched[0](description = description, command = command)
        raise ValueError(f"no unique match for description: {description!r}")


@typechecked
class CreateSnapshotTransaction(Transaction):
    """
    format: "create snapshot: HOST:DATASET@SNAPSHOT (WRITTEN)"
    """

    _PREFIX = "create snapshot: "
    _PATTERN = re.compile(
        r"^create snapshot: (?P<host>[^:]+):(?P<dataset>[^@]*)@(?P<snapshot>\S+) \((?P<written>[^)]+)\)$"
    )

    def __init__(self, description: str, **kwargs):
        super().__init__(**kwargs)
        m = self._PATTERN.fullmatch(description)
        if m is None:
            raise ValueError(f"unexpected description: {description!r}")
        self._host = m.group("host")
        self._dataset = m.group("dataset")
        self._snapshot = m.group("snapshot")
        self._written = m.group("written")

    @classmethod
    def matches(cls, description: str) -> bool:
        return description.startswith(cls._PREFIX)

    @property
    def host(self) -> str:
        return self._host

    @property
    def dataset(self) -> str:
        return self._dataset

    @property
    def snapshot(self) -> str:
        return self._snapshot

    @property
    def written(self) -> str:
        return self._written


@typechecked
class DestroySnapshotTransaction(Transaction):
    """
    format: "destroy snapshot: HOST:DATASET@SNAPSHOT"
    """

    _PREFIX = "destroy snapshot: "
    _PATTERN = re.compile(
        r"^destroy snapshot: (?P<host>[^:]+):(?P<dataset>[^@]*)@(?P<snapshot>\S+)$"
    )

    def __init__(self, description: str, **kwargs):
        super().__init__(**kwargs)
        m = self._PATTERN.fullmatch(description)
        if m is None:
            raise ValueError(f"unexpected description: {description!r}")
        self._host = m.group("host")
        self._dataset = m.group("dataset")
        self._snapshot = m.group("snapshot")

    @classmethod
    def matches(cls, description: str) -> bool:
        return description.startswith(cls._PREFIX)

    @property
    def host(self) -> str:
        return self._host

    @property
    def dataset(self) -> str:
        return self._dataset

    @property
    def snapshot(self) -> str:
        return self._snapshot


@typechecked
class DiffTransaction(Transaction):
    """
    format: "diff: HOST:DATASET@SNAPSHOT"
    """

    _PREFIX = "diff: "
    _PATTERN = re.compile(
        r"^diff: (?P<host>[^:]+):(?P<dataset>[^@]*)@(?P<snapshot>\S+)$"
    )

    def __init__(self, description: str, **kwargs):
        super().__init__(**kwargs)
        m = self._PATTERN.fullmatch(description)
        if m is None:
            raise ValueError(f"unexpected description: {description!r}")
        self._host = m.group("host")
        self._dataset = m.group("dataset")
        self._snapshot = m.group("snapshot")

    @classmethod
    def matches(cls, description: str) -> bool:
        return description.startswith(cls._PREFIX)

    @property
    def host(self) -> str:
        return self._host

    @property
    def dataset(self) -> str:
        return self._dataset

    @property
    def snapshot(self) -> str:
        return self._snapshot


@typechecked
class InventoryTransaction(Transaction):
    """
    format: "inventory: HOST:ROOT"
    """

    _PREFIX = "inventory: "
    _PATTERN = re.compile(
        r"^inventory: (?P<host>[^:]+):(?P<root>.+)$"
    )

    def __init__(self, description: str, **kwargs):
        super().__init__(**kwargs)
        m = self._PATTERN.fullmatch(description)
        if m is None:
            raise ValueError(f"unexpected description: {description!r}")
        self._host = m.group("host")
        self._root = m.group("root")

    @classmethod
    def matches(cls, description: str) -> bool:
        return description.startswith(cls._PREFIX)

    @property
    def host(self) -> str:
        return self._host

    @property
    def root(self) -> str:
        return self._root


@typechecked
class TransferIncrementalTransaction(Transaction):
    """
    format: "transfer followup: SOURCE_HOST:DATASET@FROM_SNAPSHOT..TO_SNAPSHOT->TARGET_HOST"
    """

    _PREFIX = "transfer followup: "
    _PATTERN = re.compile(
        r"^transfer followup: (?P<source_host>[^:]+):(?P<dataset>[^@]*)@(?P<from_snapshot>.+?)\.\.(?P<to_snapshot>.+?)->(?P<target_host>.+)$"
    )

    def __init__(self, description: str, **kwargs):
        super().__init__(**kwargs)
        m = self._PATTERN.fullmatch(description)
        if m is None:
            raise ValueError(f"unexpected description: {description!r}")
        self._source_host = m.group("source_host")
        self._dataset = m.group("dataset")
        self._from_snapshot = m.group("from_snapshot")
        self._to_snapshot = m.group("to_snapshot")
        self._target_host = m.group("target_host")

    @classmethod
    def matches(cls, description: str) -> bool:
        return description.startswith(cls._PREFIX)

    @property
    def source_host(self) -> str:
        return self._source_host

    @property
    def dataset(self) -> str:
        return self._dataset

    @property
    def from_snapshot(self) -> str:
        return self._from_snapshot

    @property
    def to_snapshot(self) -> str:
        return self._to_snapshot

    @property
    def target_host(self) -> str:
        return self._target_host


@typechecked
class TransferInitialTransaction(Transaction):
    """
    format: "transfer initial: SOURCE_HOST:DATASET@SNAPSHOT->TARGET_HOST"
    """

    _PREFIX = "transfer initial: "
    _PATTERN = re.compile(
        r"^transfer initial: (?P<source_host>[^:]+):(?P<dataset>[^@]*)@(?P<snapshot>.+?)->(?P<target_host>.+)$"
    )

    def __init__(self, description: str, **kwargs):
        super().__init__(**kwargs)
        m = self._PATTERN.fullmatch(description)
        if m is None:
            raise ValueError(f"unexpected description: {description!r}")
        self._source_host = m.group("source_host")
        self._dataset = m.group("dataset")
        self._snapshot = m.group("snapshot")
        self._target_host = m.group("target_host")

    @classmethod
    def matches(cls, description: str) -> bool:
        return description.startswith(cls._PREFIX)

    @property
    def source_host(self) -> str:
        return self._source_host

    @property
    def dataset(self) -> str:
        return self._dataset

    @property
    def snapshot(self) -> str:
        return self._snapshot

    @property
    def target_host(self) -> str:
        return self._target_host


@typechecked
class WhichTransaction(Transaction):
    """
    format: "which: EXECUTABLE (HOST)"
    """

    _PREFIX = "which: "
    _PATTERN = re.compile(
        r"^which: (?P<executable>.+) \((?P<host>[^)]+)\)$"
    )

    def __init__(self, description: str, **kwargs):
        super().__init__(**kwargs)
        m = self._PATTERN.fullmatch(description)
        if m is None:
            raise ValueError(f"unexpected description: {description!r}")
        self._executable = m.group("executable")
        self._host = m.group("host")

    @classmethod
    def matches(cls, description: str) -> bool:
        return description.startswith(cls._PREFIX)

    @property
    def executable(self) -> str:
        return self._executable

    @property
    def host(self) -> str:
        return self._host


@typechecked
class ZpoolListTransaction(Transaction):
    """
    format: "zpool: list (HOST)"
    """

    _PREFIX = "zpool: list ("
    _PATTERN = re.compile(
        r"^zpool: list \((?P<host>[^)]+)\)$"
    )

    def __init__(self, description: str, **kwargs):
        super().__init__(**kwargs)
        m = self._PATTERN.fullmatch(description)
        if m is None:
            raise ValueError(f"unexpected description: {description!r}")
        self._host = m.group("host")

    @classmethod
    def matches(cls, description: str) -> bool:
        return description.startswith(cls._PREFIX)

    @property
    def host(self) -> str:
        return self._host
