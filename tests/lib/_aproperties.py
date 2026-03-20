from enum import Enum, auto
from typing import Optional

from typeguard import typechecked

from ._command import Command
from ._const import NAME
from ._host import Host
from ._snapshotformat import SnapshotFormat


@typechecked
class Snap(Enum):

    always = auto()
    changed = auto()
    never = auto()

    def to_string(self) -> str:
        """
        export as string
        """

        return self.name

    @classmethod
    def from_string(cls, value: str):
        """
        import from string
        """

        try:
            return getattr(cls, value)
        except AttributeError as e:
            raise ValueError from e


@typechecked
class AProperties:
    """
    wrapper holding properties for apool datasets
    """

    def __init__(
        self,
        format_: Optional[str] = None,
        overlap: Optional[int] = None,  # >=1, -1 for keeping everything on source
        diff: Optional[bool] = None,
        threshold: Optional[int] = None,  # bytes
        snap: Optional[Snap] = None,
        sync: Optional[bool] = None
    ):
        """
        init
        """

        self._prop_format = format_
        self._prop_overlap = overlap
        self._prop_diff = diff
        self._prop_threshold = threshold
        self._prop_snap = snap
        self._prop_sync = sync

    @property
    def format_(self) -> Optional[str]:
        """
        format property
        """

        return self._prop_format

    @property
    def overlap(self) -> Optional[int]:
        """
        overlap property
        """

        return self._prop_overlap

    @property
    def diff(self) -> Optional[bool]:
        """
        diff property
        """

        return self._prop_diff

    @property
    def threshold(self) -> Optional[int]:
        """
        threshold property
        """

        return self._prop_threshold

    @property
    def snap(self) -> Optional[Snap]:
        """
        snap property
        """

        return self._prop_snap

    @property
    def sync(self) -> Optional[bool]:
        """
        sync property
        """

        return self._prop_sync

    def _set_deserialized(self, attr: str, value: str):
        """
        set property by attr name as correct type
        """

        if value == "on":
            setattr(self, attr, True)
            return
        if value == "off":
            setattr(self, attr, False)
            return

        try:
            value_ = Snap.from_string(value)
            setattr(self, attr, value_)
            return
        except ValueError:
            pass

        try:
            value_ = int(value)
            setattr(self, attr, value_)
            return
        except ValueError:
            pass

        setattr(self, attr, value)

    def _get_serialized(self, attr: str) -> Optional[str]:
        """
        get property by attr name as string
        """

        value = getattr(self, attr)
        assert value is not None

        if isinstance(value, bool):
            return "on" if value else "off"
        if isinstance(value, Snap):
            return value.to_string()
        if isinstance(value, int):
            return f"{value:d}"

        assert isinstance(value, str)
        return value

    def copy(self):
        """
        full copy
        """

        def fix_format(value):
            return f"{value:s}_" if value == "format" else value

        return type(self)(**{
            fix_format(attr[6:]): getattr(self, attr)
            for attr in dir(self)
            if attr.startswith("_prop_") and getattr(self, attr) is not None
        })

    def create(self, dataset: str, host: Host):
        """
        set properties on dataset
        """

        properties = {
            f"{NAME:s}:{attr[6:]:s}": self._get_serialized(attr)
            for attr in dir(self)
            if attr.startswith("_prop_") and getattr(self, attr) is not None
        }

        for property_, value in properties.items():
            res = Command(
                "zfs",
                "set",
                f"{property_:s}={value:s}",
                dataset,
            ).with_sudo().on_host(host).run()
            res.assert_exitcode(0)

    def matches_snapshot_name(self, name: str) -> bool:
        """
        converts chrono format specifiers to regex fragments,
        checks if name was plausibly generated from format string
        """

        return SnapshotFormat.match(name = name, format_ = self._prop_format)

    def reload(self, dataset: str, host: Host):
        """
        reload values from dataset on disk
        """

        properties = {
            f"{NAME:s}:{attr[6:]:s}": attr
            for attr in dir(self)
            if attr.startswith("_prop_")
        }

        for property_, attr in properties.items():
            res = Command("zfs", "get", "-Hp", property_, dataset).with_sudo().on_host(host).run()
            res.assert_exitcode(0)
            _, _, value, source = res.stdout.decode("utf-8").strip().split("\t")
            if source != "local":
                continue
            self._set_deserialized(attr, value)

    @classmethod
    def from_defaults(
        cls,
        format_: Optional[str] = None,
        overlap: Optional[int] = None,
        diff: Optional[bool] = None,
        threshold: Optional[int] = None,
        snap: Optional[Snap] = None,
        sync: Optional[bool] = None,
    ):
        """
        useful for default settings in root, with overrides
        """

        return cls(
            format_ = SnapshotFormat.DEFAULT if format_ is None else format_,
            overlap = 2 if overlap is None else overlap,
            diff = True if diff is None else diff,
            threshold = 12582912 if threshold is None else threshold,
            snap = Snap.changed if snap is None else snap,
            sync = True if sync is None else sync,
        )

    @classmethod
    def from_name(cls, dataset: str, host: Host):
        """
        gather status from disk
        """

        aproperties = cls()
        aproperties.reload(dataset = dataset, host = host)
        return aproperties
