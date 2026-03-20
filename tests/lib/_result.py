from json import loads
import sys
from typing import Dict, List, Optional, Tuple

from typeguard import typechecked

from ._const import NAME
from ._logs import Logs
from ._testconfig import config_is_verbose


@typechecked
class Result:
    """
    wraps and evaluates command result
    """

    def __init__(self, exitcode: int, stdout: Optional[bytes] = None, stderr: Optional[bytes] = None, timeout: bool = False, command: Optional[str] = None):
        """
        set up
        """

        self._exitcode = exitcode
        self._stdout = b"<not captured>" if stdout is None else stdout
        self._stderr = b"<not captured>" if stderr is None else stderr
        self._timeout = timeout
        self._command = command

    def __repr__(self) -> str:
        """
        representation of command result
        """

        return f"<Result exitcode={self._exitcode:d} stdout_len={len(self._stdout):d} stderr_len={len(self._stdout):d} timeout={str(self._timeout):s}>"

    @property
    def exitcode(self) -> int:
        """
        process exit code
        """

        return self._exitcode

    @property
    def is_stderr_clean(self) -> bool:
        """
        If there is stderr, it should only contain cargo warnings and nothing else.
        """

        if len(self._stderr.strip()) == 0:
            return True

        _, tool = self.split_stderr()

        return len(tool.strip()) == 0

    @property
    def stderr(self) -> bytes:
        """
        raw std err
        """

        return self._stderr

    @property
    def stdout(self) -> bytes:
        """
        raw std out
        """

        return self._stdout

    @property
    def timeout(self) -> bool:
        """
        Was the process terminated by a timeout in the test harness?
        """

        return self._timeout

    def assert_exitcode(self, value: int, print_on_fail: bool = True):
        """
        triggers assertion exception if exitcode != value
        """

        if self._exitcode == value:
            return

        if print_on_fail and not config_is_verbose():
            self.print()

        assert self._exitcode == value

    def assert_no_ssh_error(self, print_on_fail: bool = True):
        """
        triggers assertion exception if exitcode == 255, i.e. ssh error
        """

        if self._exitcode != 255:
            return

        if print_on_fail and not config_is_verbose():
            self.print()

        assert self._exitcode != 255

    def print(self):
        """
        print result to stdout
        """

        if len(self._stdout.strip()) > 0:
            self.print_stream("stdout")
        else:
            print("<stdout />")
        if len(self._stderr.strip()) > 0:
            self.print_stream("stderr")
        else:
            print("<stderr />")
        if self._command is not None:
            print(f"$ {self._command:s}")

        print(f"exitcode={self._exitcode:d} timeout={str(self._timeout):s}\n")

    def print_stream(self, name: str):
        """
        print stream
        """

        data = getattr(self, f"_{name:s}")
        if not data.endswith(b"\n"):
            data += b"\n"

        print(f"<{name.upper():s}>")
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()
        sys.stdout.flush()
        print(f"</{name.upper():s}>")

    def stdout2dicts(self, ignore_errors: bool = False) -> List[Dict]:
        """
        parse stdout into unstructured dicts
        """

        msgs = []
        lines = self._stdout.split(b"\n")

        for line in lines:
            line = line.strip(b" \t\n")
            if len(line) == 0:
                continue
            try:
                msg = loads(line)
            except Exception as e:  # pylint: disable=W0718
                if not ignore_errors:
                    raise e
                else:
                    continue
            msgs.append(msg)

        return msgs

    def stdout2logs(self, ignore_errors: bool = False) -> Logs:
        """
        parse stdout into logs
        """

        return Logs.from_raw("stdout", self._stdout, ignore_errors = ignore_errors)

    def stderr2logs(self, ignore_errors: bool = False) -> Logs:
        """
        parse stderr into logs
        """

        return Logs.from_raw("stderr", self._stderr, ignore_errors = ignore_errors)

    def split_stderr(self) -> Tuple[bytes, bytes]:
        """
        Splits stderr into cargo and tool portions, indicated by a line as follows:
        "Running `target/debug/{NAME} *`"
        """

        lines = self._stderr.split(b"\n")

        target = None
        for idx, line in enumerate(lines):
            line = line.strip(b" \t\n")
            if all((
                line.startswith(b"Running"),
                f"target/debug/{NAME:s}".encode("utf-8") in line,
                line.endswith(b"`"),
            )):
                target = idx
                break

        if target is None:
            return b"", self._stderr

        return b"\n".join(lines[:target]), b"\n".join(lines[target + 1:])
