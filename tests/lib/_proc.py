from shlex import join
from subprocess import Popen, PIPE
from typing import Dict, List, Optional

from typeguard import typechecked

from ._result import Result


@typechecked
class Proc:
    """
    minimal process wrapper
    """

    def __init__(
        self,
        fragments: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict] = None,
    ):
        """
        set up
        """

        self._fragments = fragments
        self._cwd = cwd
        self._env = env

        self._proc = None

    def __repr__(self) -> str:
        """
        interactive representation
        """

        return f"<Proc proc={repr(self._proc):s}>"

    @property
    def alive(self) -> bool:
        """
        is process still running
        """

        return self._proc.poll() is None

    @property
    def proc(self) -> Optional[Popen]:
        """
        access to process
        """

        return self._proc

    def start(self):
        """
        start process
        """

        self._proc = Popen(
            self._fragments,
            stdout = PIPE,
            stderr = PIPE,
            cwd = self._cwd,
            env = self._env,
        )

    def result(self) -> Result:
        """
        get process result
        """

        stdout, stderr = self._proc.communicate()

        return Result(
            exitcode=self._proc.returncode,
            stdout=stdout,
            stderr=stderr,
            timeout=False,
            command=join(self._fragments),
        )

    def stop(self) -> Result:
        """
        kill process
        """

        self._proc.terminate()
        self._proc.wait()
        return self.result()
