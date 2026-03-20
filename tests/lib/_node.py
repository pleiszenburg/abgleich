from typing import Any, Iterator

from typeguard import typechecked

from ._command import Command
from ._host import Host
from ._path import Path
from ._testconfig import TestConfig
from ._zpool import Zpool


@typechecked
class Node:
    """
    represents one node, i.e. one VM, in test setup
    """

    def __init__(self, host: Host, testconfig: TestConfig):
        """
        base setup for node, no action is yet taken
        """

        self._host = host
        self._testconfig = testconfig

        self._open = False

        self._zpools = {}
        self._zpools_system = self.get_ondisk_zpool_names()

        self._root = Path(self._get_config("root")).to_abs(self._host)

    def __getitem__(self, name: str) -> Zpool:
        """
        access zpool by name
        """

        return self._zpools[name]

    @property
    def host(self) -> Host:
        return self._host

    @property
    def is_open(self) -> bool:
        """
        is node open
        """

        return self._open

    @property
    def required(self) -> bool:
        """
        is node required for test and needs to be opened and closed
        """

        return self._get_config("required")

    @property
    def root(self) -> Path:
        """
        root path of test session
        """

        return self._root

    @property
    def zpools(self) -> Iterator[Zpool]:
        """
        iterator over zpools
        """

        return (zpool for zpool in self._zpools.values())

    def _get_config(self, key: str) -> Any:
        """
        extract config value
        """

        return self._testconfig[f"nodes/{self._host.to_config_name():s}/{key:s}"]

    def close(self, force: bool = False):
        """
        destroy resources on node
        """

        if not self._open and not force:
            raise ValueError("node not open")

        self._open = False

        for zpool in self._zpools.values():
            zpool.destroy(self._host)
        self._zpools.clear()

        self._root.rmdir_safe(host = self._host, description = "test session root folder")

    def get_ondisk_zpool_names(self) -> set[str]:
        """
        get set of existing zpools
        """

        res = Command("zpool", "list", "-Hp").with_sudo().on_host(self._host).run()
        res.assert_exitcode(0)

        return {
            line.split("\t")[0]
            for line in res.stdout.decode("utf-8").split("\n")
            if len(line.strip()) > 0
        }

    def open(self):
        """
        create resources on node
        """

        if self._open:
            raise ValueError("node already open")

        self._root.mkdir(self._host).chmod(self._host, "777")

        self._zpools.clear()
        self._zpools.update({
            zpool.name: zpool.copy()
            for zpool in self._get_config("zpools")
        })
        for zpool in self._zpools.values():
            zpool.create(host = self._host, root = self.root.value)

        self._open = True

    def reload(self):
        """
        reload resources on node for validation
        """

        if not self._open:
            raise ValueError("node not open")

        names = self.get_ondisk_zpool_names() - self._zpools_system

        for name in set(self._zpools.keys()):
            if name not in names:
                self._zpools.pop(name)  # drop old ones

        for name in names:
            if name in self._zpools.keys():
                self._zpools[name].reload(host = self._host)  # update existing
            else:
                self._zpools[name] = Zpool.from_name(name, host = self._host)  # add new ones

    def sync(self):
        """
        force sync on zpools
        """

        res = Command("zpool", "sync").with_sudo().on_host(self._host).run()
        res.assert_exitcode(0)
