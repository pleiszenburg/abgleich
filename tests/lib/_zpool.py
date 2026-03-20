from typing import Optional
import os

from typeguard import typechecked

from ._command import Command
from ._filesystem import Filesystem
from ._host import Host
from ._mountpoint import Mountpoint, MntLocal, MntInherit
from ._path import Path


@typechecked
class Zpool(Filesystem):
    """
    description of a zpool and root filesystem, allowing to create and destroy it
    """

    def __init__(
        self,
        *args,
        name: str,
        fn: Optional[str] = None,  # storage backend
        size: int = 1 * 1024 ** 3,  # 1 GByte
        ashift: int = 12,
        compression: bool = True,
        mountpoint: Mountpoint = MntInherit(),
        **kwargs,
    ):
        """
        init
        """

        if isinstance(mountpoint, MntInherit):
            mountpoint = MntLocal(name)

        super().__init__(
            *args,
            name = name,
            mountpoint = mountpoint,
            **kwargs,
        )

        assert ashift > 0
        assert size > 0

        self._fn = fn
        self._size = size
        self._ashift = ashift
        self._compression = compression

        self._fn_abs = None

    @property
    def ashift(self) -> int:
        """
        zpool option
        """

        return self._ashift

    @property
    def compression(self) -> bool:
        """
        dataset option
        """

        return self._compression

    @property
    def full_name(self) -> str:
        """
        full zfs name of dataset
        """

        return self._name

    @property
    def fn(self) -> Optional[str]:
        """
        path to file backing up the file system
        """

        return self._fn

    @property
    def fn_abs(self) -> Optional[str]:
        """
        absolut path to file backing up the file system
        only available while zpool exists
        """

        return self._fn_abs

    @property
    def size(self) -> int:
        """
        size of storage backing up file system
        """

        return self._size

    @staticmethod
    def _get_ondisk_property(zpool: str, property_: str, host: Host) -> str:  # pylint: disable=W0237
        """
        get ondisk value of property as string
        """

        res = Command("zpool", "get", "-Hp", property_, zpool).with_sudo().on_host(host).run()
        res.assert_exitcode(0)
        return res.stdout.decode("utf-8").strip().split("\t")[2]

    def copy(self):
        """
        full copy
        """

        return type(self)(
            fn = self._fn,
            size = self._size,
            ashift = self._ashift,
            compression = self._compression,
            **self._copy_filesystem(),
        )

    def create(self, host: Host, root: str):  # pylint: disable=W0237
        """
        create zpool
        """

        fn = f"{self._name:s}.bin" if self._fn is None else self._fn
        self._fn_abs = os.path.join(root, fn) if not os.path.isabs(fn) else fn
        Path(self._fn_abs).allocate(host = host, size = self._size).chmod(host = host, permissions = "666")

        self._mountpoint_abs = self._mountpoint.to_value_abs(root)
        if self._mountpoint_abs is not None:
            Path(self._mountpoint_abs).mkdir(host)

        res = Command(
            "zpool",
            "create",
            "-o", f"ashift={self._ashift:d}",
            "-O", "atime=on",  # force for consistent behaviour
            "-O", "relatime=off",  # force for consistent behaviour
            "-O", f"compression={'on' if self._compression else 'off':s}",
            "-m", self._mountpoint.to_option_abs(root),
            self._name,
            self._fn_abs,
        ).with_sudo().on_host(host).run()
        res.assert_exitcode(0)

        self._create_children(host = host)

    def destroy(self, host: Host):  # pylint: disable=W0221
        """
        destroy zpool
        """

        if self._name.startswith("data"):  # developer's note: my production zpools are prefixed with `data`
            raise ValueError("do not kill my data")

        self._destroy_children(host = host)

        res = Command(
            "zpool",
            "destroy",
            "-f",  # TODO is this a good idea?
            self._name,
        ).with_sudo().on_host(host).run()
        res.assert_exitcode(0)

        if self._mountpoint_abs is not None:
            Path(self._mountpoint_abs).rmdir_safe(host = host, description = f"mountpoint for zpool {self._name:s}")
        self._mountpoint_abs = None

        path = Path(self._fn_abs)
        if path.exists(host):
            path.rm(host)

        self._fn_abs = None

    def reload(self, host: Host):  # pylint: disable=W0246
        """
        reload zpool and children
        """

        # zpool properties unlikely to change
        super().reload(host = host)

    @classmethod
    def from_name(cls, name: str, host: Host):  # pylint: disable=W0221
        """
        from zpool on disk based on name
        """

        zpool = cls(
            name = name,
            fn = None,  # can not (easily) determined from a pool
            size = 0,  # can not (easily) determined from a pool
            ashift = int(cls._get_ondisk_property(name, "ashift", host = host)),
        )
        zpool.reload(host = host)
        return zpool
