from typing import Optional
import os

from typeguard import typechecked

from ._command import Command
from ._dataset import Dataset
from ._host import Host
from ._mountpoint import Mountpoint, MntInherit


@typechecked
class Filesystem(Dataset):
    """
    describes a zfs dataset of type filesystem
    """

    def __init__(
        self,
        *args,
        mountpoint: Mountpoint = MntInherit(),
        **kwargs,
    ):
        """
        init
        """

        super().__init__(*args, **kwargs)

        self._mountpoint = mountpoint

        self._mountpoint_abs = None

    @property
    def mountpoint(self) -> Mountpoint:
        """
        mountpoint option of zpool
        """

        return self._mountpoint

    @property
    def mountpoint_abs(self) -> Optional[str]:
        """
        absolut path to mountpoint of filesystem
        only available while zpool/filesystem exists
        """

        return self._mountpoint_abs

    def copy(self):
        """
        full copy
        """

        return type(self)(
            **self._copy_filesystem(),
        )

    def _copy_filesystem(self):
        """
        filesystem copy
        """

        return dict(
            mountpoint = self._mountpoint,
            **self._copy_base(),
        )

    def create(self, host: Host, parent: Dataset):  # pylint: disable=W0222
        """
        create dataset
        """

        super().create(host = host, parent = parent)

        if isinstance(self._mountpoint, MntInherit):
            if isinstance(parent, Filesystem):
                if parent.mountpoint_abs is None:
                    self._mountpoint_abs = None
                else:
                    self._mountpoint_abs = os.path.join(parent.mountpoint_abs, self._name)
            else: # volume
                self._mountpoint_abs = None  # TODO check volume/filesystem with inheritance of mountpoint, what happens?
            mount_args = tuple()
        else:
            self._mountpoint_abs = self._mountpoint.value
            mount_args = ("-o", f"mountpoint={self._mountpoint.to_option():s}")

        res = Command(
            "zfs",
            "create",
            *mount_args,
            self.full_name,
        ).with_sudo().on_host(host).run()
        res.assert_exitcode(0)

        self._create_children(host = host)

    def destroy(self, host: Host):
        """
        destroy dataset
        """

        self._destroy_children(host = host)

        res = Command(
            "zfs",
            "destroy",
            self.full_name,
        ).with_sudo().on_host(host).run()
        res.assert_exitcode(0)

        self._mountpoint_abs = None

        super().destroy(host = host)

    def reload(self, host: Host):
        """
        reload filesystem and children
        """

        self._mountpoint = Mountpoint.from_disk(self.full_name, host = host)

        super().reload(host = host)

    @classmethod
    def from_name(cls, name: str, parent: Dataset, host: Host):
        """
        from on-disk filesystem
        """

        filesystem = cls(
            name = name,
        )
        filesystem.parent = parent
        filesystem.reload(host = host)

        return filesystem
