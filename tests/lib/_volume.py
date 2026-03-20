from typing import Optional

from typeguard import typechecked

from ._command import Command
from ._dataset import Dataset
from ._host import Host


@typechecked
class Volume(Dataset):
    """
    describes a zfs dataset of type volume
    """

    def __init__(
        self,
        *args,
        size: int,  # bytes
        blocksize: Optional[int] = None,
        sparse: bool = False,
        **kwargs,
    ):
        """
        init
        """

        super().__init__(*args, **kwargs)

        self._size = size
        self._blocksize = blocksize
        self._sparse = sparse

    @property
    def blocksize(self) -> Optional[int]:
        """
        size of volume block (volblocksize), by ZFS >= 2.2 it's 16k
        """

        return self._blocksize

    @property
    def sparse(self) -> bool:
        """
        is volume sparse
        """

        return self._sparse

    @property
    def size(self) -> int:
        """
        size of volume
        """

        return self._size

    def copy(self):
        """
        full copy
        """

        return type(self)(
            size = self._size,
            blocksize = self._blocksize,
            sparse = self._sparse,
            **self._copy_base(),
        )

    def create(self, host: Host, parent: Dataset):  # pylint: disable=W0222
        """
        create dataset
        """

        super().create(host = host, parent = parent)

        sparse_args = ("-s",) if self._sparse else tuple()
        blocksize_args = tuple() if self._blocksize is None else ("-o", f"volblocksize={self._blocksize:d}")

        res = Command(
            "zfs",
            "create",
            *sparse_args,
            *blocksize_args,
            "-V", f"{self._size:d}",
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

    def reload(self, host: Host):  # pylint: disable=W0246
        """
        reload volume and children
        """

        # properties should not change unless volume is re-created under same name
        super().reload(host = host)

    @classmethod
    def from_name(cls, name: str, parent: Dataset, host: Host):
        """
        from on-disk volume
        """

        full_name = f"{parent.full_name:s}/{name:s}"

        def get_prop(property_: str) -> str:
            res = Command("zfs", "get", property_, "-Hp", full_name).with_sudo().on_host(host).run()
            res.assert_exitcode(0)
            return res.stdout.decode("utf-8").strip().split("\t")[2]

        volume = cls(
            name = name,
            size = int(get_prop("size")),
            blocksize = int(get_prop("volblocksize")),
            sparse = get_prop("refreservation") != "auto",
        )
        volume.parent = parent
        volume.reload(host = host)

        return volume
