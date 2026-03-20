from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Iterator, List, Optional

from typeguard import typechecked

from ._aproperties import AProperties
from ._command import Command
from ._host import Host
from ._repr import repr_tree
from ._snapshot import Snapshot


@typechecked
class Dataset(ABC):
    """
    zfs dataset base class
    """

    @abstractmethod
    def __init__(
        self,
        name: str,
        datasets: "Optional[List[Dataset]]" = None,
        snapshots: Optional[List[Snapshot]] = None,
        aproperties: Optional[AProperties] = None,
    ):
        """
        init
        """

        self._name = name
        self._datasets = {} if datasets is None else {dataset.name: dataset for dataset in datasets}
        self._snapshots = {} if snapshots is None else OrderedDict((snapshot.name, snapshot) for snapshot in snapshots)
        self._aproperties = AProperties() if aproperties is None else aproperties

        self._parent = None

    def __repr__(self) -> str:
        """
        interactive representation
        """

        return repr_tree(
            base = f"<{type(self).__name__:s} name={self._name:s}>",
            branches = dict(
                datasets = self._datasets,
                snapshots = self._snapshots,
            ),
        )

    def __truediv__(self, name: str) -> "Dataset":
        """
        child dataset based on name
        """

        return self._datasets[name]

    def __matmul__(self, name: str) -> "Snapshot":
        """
        child snapshot based on name
        """

        return self._snapshots[name]

    @property
    def name(self) -> str:
        """
        name of dataset
        """

        return self._name

    @property
    def full_name(self) -> str:
        """
        full zfs name of dataset
        """

        if self._parent is None:
            raise ValueError("dataset is currently not on disk")

        return f"{self._parent.full_name:s}/{self._name:s}"

    @property
    def aproperties(self) -> AProperties:
        """
        specific abgleich zfs dataset properties
        """

        return self._aproperties

    @property
    def datasets(self) -> "Iterator[Dataset]":
        """
        datasets
        """

        return (dataset for dataset in self._datasets.values())

    @property
    def parent(self) -> "Optional[Dataset]":
        """
        parent
        """

        return self._parent

    @parent.setter
    def parent(self, value: "Optional[Dataset]"):
        """
        parent
        """

        self._parent = value

    @property
    def snapshots(self) -> Iterator[Snapshot]:
        """
        snapshots
        """

        return (snapshot for snapshot in self._snapshots.values())

    def _copy_base(self):
        """
        full copy of common base properties
        """

        return dict(
            name = self._name,
            datasets = [dataset.copy() for dataset in self.datasets],
            snapshots = [snapshot.copy() for snapshot in self.snapshots],
            aproperties = self._aproperties.copy(),
        )

    def _create_children(self, host: Host):
        """
        create children of dataset
        """

        self._aproperties.create(dataset = self.full_name, host = host)

        for dataset in self.datasets:
            dataset.create(parent = self, host = host)
        for snapshot in self.snapshots:
            snapshot.create(parent = self, host = host)

    def _destroy_children(self, host: Host):
        """
        destroy children of dataset
        """

        for snapshot in self.snapshots:
            snapshot.destroy(host = host)
        for dataset in self.datasets:
            dataset.destroy(host = host)

    @abstractmethod
    def copy(self):
        """
        full copy
        """

    @abstractmethod
    def create(self, host: Host, parent: "Optional[Dataset]" = None):
        """
        create dataset
        """

        self._parent = parent

    @abstractmethod
    def destroy(self, host: Host):
        """
        destroy dataset
        """

        self._parent = None

    def get_ondisk_dataset_names(self, host: Host) -> List[str]:
        """
        list all child datasets by name of parent dataset
        """

        res = Command("zfs", "list", "-Hp", "-d", "1", self.full_name).with_sudo().on_host(host).run()
        res.assert_exitcode(0)
        return [
            line.split("\t")[0].split("/")[-1]
            for idx, line in enumerate(res.stdout.decode("utf-8").split("\n"))
            if len(line.strip()) > 0 and idx > 0
        ]

    @staticmethod
    def _get_ondisk_property(dataset: str, property_: str, host: Host) -> str:
        """
        get ondisk value of property as string
        """

        res = Command("zfs", "get", "-Hp", property_, dataset).on_host(host).run()
        res.assert_exitcode(0)
        return res.stdout.decode("utf-8").strip().split("\t")[2]

    def get_ondisk_snapshot_names(self, host: Host) -> List[str]:
        """
        list all child snapshots by name of parent dataset
        """

        res = Command("zfs", "list", "-Hp", "-t", "snapshot", self.full_name).with_sudo().on_host(host).run()
        res.assert_exitcode(0)
        return [
            line.split("\t")[0].split("@")[1]
            for line in res.stdout.decode("utf-8").split("\n")
            if len(line.strip()) > 0
        ]

    @abstractmethod
    def reload(self, host: Host):
        """
        reload dataset and children
        """

        self._aproperties.reload(dataset = self.full_name, host = host)

        dataset_names = self.get_ondisk_dataset_names(host = host)

        for name in dataset_names:
            if name in self._datasets.keys():
                self._datasets[name].reload(host = host)
            else:
                self._datasets[name] = Dataset.from_name(name, parent = self, host = host)
        for name in set(self._datasets.keys()):
            if name not in dataset_names:
                self._datasets.pop(name)

        assert set(self._datasets.keys()) == set(dataset_names)

        snapshot_names = self.get_ondisk_snapshot_names(host = host)

        for name in snapshot_names:
            if name in self._snapshots.keys():
                self._snapshots[name].reload(host = host)
            else:
                self._snapshots[name] = Snapshot.from_name(name, parent = self, host = host)
        for name in set(self._snapshots.keys()):
            if name not in snapshot_names:
                self._snapshots.pop(name)

        assert set(self._snapshots.keys()) == set(snapshot_names)

        sorted_snapshots = OrderedDict((name, self._snapshots[name]) for name in snapshot_names)
        self._snapshots.clear()
        self._snapshots.update(sorted_snapshots)

    @classmethod
    def from_name(cls, name: str, parent: "Dataset", host: Host):
        """
        filesystem/volume from name
        """

        full_name = f"{parent.name:s}/{name:s}"
        type_ = cls._get_ondisk_property(full_name, "type", host = host)

        if type_ == "filesystem":
            from ._filesystem import Filesystem
            return Filesystem.from_name(name, parent, host = host)

        if type_ == "volume":
            from ._volume import Volume
            return Volume.from_name(name, parent, host = host)

        raise ValueError(f"unknown dataset type {type_:s}")
