from enum import Enum, auto
import os

from typeguard import typechecked

from ._const import NAME, DEFAULT_TARGET
from ._platform import Platform
from ._testconfig import config_release, config_target


@typechecked
class Target(Enum):
    """
    set compiler/binary target for test suite
    """

    if Platform.current is Platform.linux:
        x86_64_unknown_linux_gnu = auto()
        x86_64_unknown_linux_musl = auto()

    if Platform.current is Platform.freebsd:
        x86_64_unknown_freebsd = auto()

    def to_run_cmd(self) -> str:
        """
        translate to command to run abgleich
        """

        fld = "release" if config_release() else "debug"

        if Platform.current is Platform.linux and self is self.x86_64_unknown_linux_gnu:
            return os.path.abspath(os.path.join(
                os.getcwd(),
                f"target/x86_64-unknown-linux-gnu/{fld:s}/{NAME:s}",
            ))

        if Platform.current is Platform.linux and self is self.x86_64_unknown_linux_musl:
            return os.path.abspath(os.path.join(
                os.getcwd(),
                f"target/x86_64-unknown-linux-musl/{fld:s}/{NAME:s}",
            ))

        if Platform.current is Platform.freebsd and self is self.x86_64_unknown_freebsd:
            return os.path.abspath(os.path.join(
                os.getcwd(),
                f"target/x86_64-unknown-freebsd/{fld:s}/{NAME:s}",
            ))

        raise ValueError("target currently not supported for direct test suite run", self.name)

    @classmethod
    def from_env_str(cls, data: str) -> "Target":
        """
        translate string to enum
        """

        data = data.lower().strip()

        if Platform.current is Platform.linux and data == "x86_64-unknown-linux-gnu":
            return cls.x86_64_unknown_linux_gnu

        if Platform.current is Platform.linux and data in ("x86_64-unknown-linux-musl", DEFAULT_TARGET):
            return cls.x86_64_unknown_linux_musl

        if Platform.current is Platform.freebsd and data in ("x86_64-unknown-freebsd", DEFAULT_TARGET):
            return cls.x86_64_unknown_freebsd

        raise ValueError("unknown target", data)

    @classmethod
    def from_env_var(cls) -> "Target":
        """
        get current target from env var
        """

        return cls.from_env_str(config_target())
