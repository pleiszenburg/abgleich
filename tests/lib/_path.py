import os
from typing import Optional, Self
from warnings import warn
from typing import Any

from typeguard import typechecked

from ._command import Command
from ._host import Host


_COMPRESSIBLE_DATA = "10000000000000000000000"


@typechecked
class Path:
    """
    wraps shell and ssh commands for file / directory operations
    """

    def __init__(self, value: str):
        self._value = value

    def __truediv__(self, other: Any) -> Self:
        """
        append another path fragment to new path
        """

        if isinstance(other, type(self)):
            return type(self)(os.path.join(self._value, other.value))

        if isinstance(other, str):
            return type(self)(os.path.join(self._value, other))

        return NotImplemented

    @property
    def value(self) -> str:
        """
        path as string
        """

        return self._value

    def allocate(self, host: Host, size: int) -> Self:
        """
        create empty (zeros) file of given size
        """

        if self.exists(host):
            raise ValueError(f"{self._value:s} already exists")

        res = Command(
            "dd",
            "if=/dev/zero",
            f"of={self._value:s}",
            "count=1", "bs=1", f"seek={size-1:d}",
        ).with_sudo().on_host(host).run()
        res.assert_exitcode(0)

        return self

    def chmod(self, host: Host, permissions: str) -> Self:
        """
        chmod command
        """

        res = Command("chmod", permissions, self._value).with_sudo().on_host(host).run()
        res.assert_exitcode(0)

        return self

    def compressible(self, host: Host, size: int) -> Self:
        """
        create file of given size with easily compressible data
        """

        res = Command("truncate", "-s", "0", self._value).with_sudo().on_host(host).run()  # implicitly also creates file
        res.assert_exitcode(0)

        res = Command(
            "bash", "-c", f'yes "{_COMPRESSIBLE_DATA}" | head -c {size:d} > {self._value:s}'
        ).with_sudo().on_host(host).run()
        res.assert_exitcode(0)

        return self

    def create_file(self, host: Host, content: str):
        """
        write content to new or truncated file
        """

        if host is not Host.localhost:
            raise ValueError("remote file write not yet supported")

        with open(self._value, mode = "w", encoding = "utf-8") as f:
            f.write(content)

    def is_file(self, host: Host) -> bool:
        """
        check if path exists and is file
        """

        res = Command("test", "-f", self._value).with_sudo().on_host(host).run()  # is file?
        res.assert_no_ssh_error()

        return res.exitcode == 0

    def join(self, *other: str) -> Self:
        """
        join new element to path
        """

        return type(self)(os.path.join(self._value, *other))

    def exists(self, host: Host) -> bool:
        """
        check if path exists
        """

        res = Command("test", "-e", self._value).with_sudo().on_host(host).run()  # is file?
        res.assert_no_ssh_error()

        return res.exitcode == 0

    def listdir(self, host) -> list[str]:
        """
        os.listdir
        """

        res = Command("ls", "-1", self._value).with_sudo().on_host(host).run()
        res.assert_exitcode(0)

        return [entry for entry in res.stdout.decode("utf-8").strip(" \t\n").split("\n") if len(entry) > 0]

    def mkdir(self, host: Host) -> Self:
        """
        mkdir command
        """

        res = Command("mkdir", self._value).with_sudo().on_host(host).run()
        res.assert_exitcode(0)

        return self

    def randomize(self, host: Host, count: int = 1, bs: int = (2 ** 10) ** 2) -> Self:
        """
        create file of given block size and block count filled with random data
        """

        if self.exists(host):
            raise ValueError(f"{self._value:s} already exists")

        res = Command(
            "dd",
            "if=/dev/urandom",
            f"of={self._value:s}",
            f"count={count:d}", f"bs={bs}",
        ).with_sudo().on_host(host).run()
        res.assert_exitcode(0)

        return self

    def rm(self, host: Host, recursive: bool = False) -> Self:
        """
        rm command
        """

        args = ("-r",) if recursive else tuple()

        res = Command("rm", *args, self._value).with_sudo().on_host(host).run()
        res.assert_exitcode(0)

        return self

    def rmdir(self, host: Host) -> Self:
        """
        rmdir command
        """

        res = Command("rmdir", self._value).with_sudo().on_host(host).run()
        res.assert_exitcode(0)

        return self

    def rmdir_safe(self, host: Host, description: str) -> Self:
        """
        rmdir command, recursive, but also checks and warns
        """

        if not self.exists(host):
            warn(f"{description:s} '{self._value:s}' did not exist unexpectedly on host {host.to_host_name():s}")
            return self

        entries = self.listdir(host)
        if len(entries) > 0:
            warn(f"{description:s} '{self._value:s}' contains unexpected items after cleanup on host {host.to_host_name():s}: {repr(entries):s}")
            return self.rm(host = host, recursive = True)

        return self.rmdir(host)

    def to_abs(self, host: Host) -> Self:
        """
        if path is relative, turn into absolute path
        """

        if os.path.isabs(self._value):
            return self

        pwd = type(self).from_pwd(host)
        return type(self)(
            os.path.abspath(os.path.join(pwd.value, self._value))
        )

    def touch(self, host: Host) -> Self:
        """
        touch command
        """

        res = Command("touch", self._value).with_sudo().on_host(host).run()
        res.assert_exitcode(0)

        return self

    def unlink(self, host: Host) -> Self:
        """
        rm command
        """

        res = Command("unlink", self._value).with_sudo().on_host(host).run()
        res.assert_exitcode(0)

        return self

    @classmethod
    def from_pwd(cls, host: Host, user: Optional[str] = None) -> Self:
        """
        run pwd on host
        """

        res = Command("pwd").with_user(user).on_host(host).run()
        res.assert_exitcode(0)

        return cls(res.stdout.decode("utf-8").strip())
