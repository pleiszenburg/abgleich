from shlex import join, quote
from subprocess import Popen, PIPE, TimeoutExpired
from typing import Dict, Iterator, Optional, Union

from typeguard import typechecked

from ._host import Host
from ._proc import Proc
from ._result import Result


@typechecked
class Command:
    """
    command runner
    """

    def __init__(self, *fragments: str, env: Optional[Dict] = None):
        """
        set up
        """

        self._fragments = fragments
        self._env = env

    def __repr__(self) -> str:
        """
        interactive representation
        """

        return f"<Cmd fragments={repr(self._fragments):s}>"

    @property
    def fragments(self) -> Iterator[str]:
        """
        command fragments
        """

        return (fragment for fragment in self._fragments)

    @staticmethod
    def _cp_env(env: Optional[Dict] = None) -> Optional[Dict]:
        """
        generate env variables from os.environ
        """

        if env is None:
            return None
        return env.copy()

    def copy(self) -> "Command":
        """
        copy command
        """

        return type(self)(*self._fragments, env = None if self._env is None else self._env.copy())

    def on_host(self, host: Host, **options) -> "Command":
        """
        rewrite command into remotely ssh-triggered command
        """

        if host is Host.localhost:
            return self.copy()

        def _fix_quotes(fragment: str) -> str:
            fragment = quote(fragment)
            if fragment.startswith("="):  # HACK not automatically quoted
                return f"'{fragment:s}'"
            return fragment

        return type(self)(
            "ssh",
            *(
                fragment
                for name, value in options.items()
                for fragment in ("-o", f"{name:s}={quote(value):s}")
            ),
            host.to_host_name(),
            *(
                f"{name:s}={quote(value):s}"
                for name, value in ({}.items() if self._env is None else self._env.items())
            ),
            *(
                _fix_quotes(fragment) if len(fragment) > 0 else "''"
                for fragment in self._fragments
            ),
            env = None,
        )

    def with_env(self, env: Dict) -> "Command":
        """
        new command with environment
        """

        new_env = {} if self._env is None else self._env.copy()
        new_env.update(env)
        return type(self)(*self._fragments, env = new_env)

    def with_sudo(self) -> "Command":
        """
        prefix command with "sudo"
        """

        return type(self)("sudo", *self._fragments, env = None if self._env is None else self._env.copy())

    def with_user(self, name: Optional[str] = None) -> "Command":
        """
        prefix command with "sudo" for specific user
        """

        if name is None:  # preserve current user
            return self.copy()

        if name == "root":
            return self.with_sudo()

        env = []
        if self._env is not None:
            env.extend((f"{key:s}={value:s}" for key, value in self._env.items()))

        return type(self)("sudo", "-u", name, *env, *self._fragments)

    def run(
        self,
        stdin: Optional[bytes] = None,
        timeout: Optional[int] = None,
        cwd: Optional[str] = None,
        capture_stdout: bool = True,
        capture_stderr: bool = True,
        interactive: bool = False,
    ) -> Result:
        """
        run command, return result
        """

        fragments = list(self._fragments)

        proc = Popen(
            fragments,
            stdout = PIPE if capture_stdout else None,
            stderr = PIPE if capture_stderr else None,
            stdin = PIPE if stdin is not None else None,
            cwd = cwd,
            env = self._cp_env(self._env),
        )

        if interactive:
            proc.wait()
            return Result(
                exitcode=proc.returncode,
                stdout=None,
                stderr=None,
                timeout=False,
                command=join(self._fragments),
            )

        hit_timeout = False
        if timeout is None:
            stdout, stderr = proc.communicate(input = stdin)
        else:
            try:
                stdout, stderr = proc.communicate(input = stdin, timeout = timeout)
            except TimeoutExpired:
                proc.kill()
                hit_timeout = True
                stdout, stderr = proc.communicate()

        return Result(
            exitcode=proc.returncode,
            stdout=stdout,
            stderr=stderr,
            timeout=hit_timeout,
            command=join(self._fragments),
        )

    def run_background(
        self,
        stdin: Optional[bytes] = None,
        timeout: Optional[int] = None,
        cwd: Optional[str] = None,
    ) -> Iterator[Union[Result, int, None]]:
        """
        run command, yield None after launch, yield result after
        """

        fragments = list(self._fragments)

        proc = Popen(
            fragments,
            stdout = PIPE,
            stderr = PIPE,
            stdin = PIPE if stdin is not None else None,
            cwd = cwd,
            env = self._cp_env(self._env),
        )
        yield None

        hit_timeout = False
        if timeout is None:
            stdout, stderr = proc.communicate(input = stdin)
        else:
            try:
                stdout, stderr = proc.communicate(input = stdin, timeout = timeout)
            except TimeoutExpired:
                proc.kill()
                hit_timeout = True
                stdout, stderr = proc.communicate()

        yield Result(
            exitcode=proc.returncode,
            stdout=stdout,
            stderr=stderr,
            timeout=hit_timeout,
        )

    def background(
        self,
        cwd: Optional[str] = None,
    ) -> Proc:
        """
        run command, return proc
        """

        fragments = list(self._fragments)

        proc = Proc(
            fragments,
            cwd = cwd,
            env = self._cp_env(self._env),
        )
        proc.start()
        return proc
