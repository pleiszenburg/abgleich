from json import loads
import logging
import os
import re
from shlex import join, split
from shutil import get_terminal_size
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from termcolor import colored
from typeguard import typechecked

from ._command import Command
from ._config import Config
from ._description import ApoolDescription, EntryDescription
from ._const import CONFIG_FN, NAME, TRACEBACK_SEP
from ._host import Host
from ._msg import Msg
from ._node import Node
from ._repr import repr_tree
from ._result import Result
from ._shell import shell
from ._subcmd import Subcmd
from ._target import Target
from ._testconfig import TestConfig, config_is_verbose, config_log_to_disk
from ._transaction import Transaction


@typechecked
class Context:
    """
    test context, used to create, manage, investigate and destroy test environments
    """

    def __init__(self, testconfig: TestConfig):
        """
        set up context based on configuration
        """

        self._testconfig = testconfig

        self._open = False
        self._width = get_terminal_size().columns

        self._nodes = {
            host: Node(host = host, testconfig = self._testconfig)
            for host in (
                Host.from_config_name(name)
                for name in self._testconfig.nodes
            )
        }

    def __repr__(self) -> str:
        """
        interactive representation
        """

        return repr_tree(
            base = f"<Context open={str(self._open):s}>",
            branches = dict(
                cfg = self._testconfig,
            ),
        )

    def __getitem__(self, host: Host) -> Node:
        """
        access node by host
        """

        return self._nodes[host]

    @property
    def config(self) -> Config:
        """
        abgleich configuration
        """

        return self._testconfig["abgleich"]

    @property
    def is_open(self) -> bool:
        """
        is context open
        """

        return self._open

    @property
    def target(self) -> str:
        """
        command to run to tool
        """

        return Target.from_env_var().to_run_cmd()

    @property
    def testconfig(self) -> TestConfig:
        """
        test configuration
        """

        return self._testconfig

    @staticmethod
    def _get_next_log_filename():
        """
        enumerate file names for dumping output
        """

        fns = [fn for fn in os.listdir(".") if fn.startswith(f".{NAME:s}_")]
        idx = 0 if len(fns) == 0 else max([int(fn.split("_")[1]) for fn in fns]) + 1
        return f".{NAME:s}_{idx:05d}"

    def _get_env(
        self,
        host: Host,
        user: Optional[str] = None,
        incl_os_env: bool = False,
        os_env_matches: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        generate default env variables for abgleich
        """

        env = self._get_os_env(host = host, user = user, os_env_matches = os_env_matches) if incl_os_env else {}

        env.update(dict(
            ABGLEICH_LOGLEVEL = str(self._testconfig["abgleich/loglevel"]),
        ))

        return env

    @staticmethod
    def _get_os_env(host: Host, user: Optional[str] = None, os_env_matches: Optional[str] = None) -> Dict[str, str]:
        """
        get an optionally down-selected copy of environment variable variables
        """

        res = Command("env").with_user(user).on_host(host).run()
        res.assert_exitcode(0)

        env = dict((
            line.strip().split("=", maxsplit = 1)
            for line in res.stdout.decode("utf-8").strip().split("\n")
            if len(line.strip()) > 0
        ))

        if os_env_matches is not None:
            pattern = re.compile(os_env_matches)
            env = {
                key: value for key, value in env.items()
                if pattern.match(key)
            }

        return env

    @staticmethod
    def parse_raw_table(table: bytes) -> List[Dict[str, Optional[str]]]:
        """
        parse raw table into list of dicts

        Column boundaries are determined once from the header row, whose column
        names are guaranteed not to contain '|', and then reused for every data
        row.  Slicing by fixed position (rather than splitting on '|') means
        that literal '|' characters inside a cell value — such as a shell pipe
        in a command string — do not disrupt column alignment.

        ANSI escape sequences are stripped before processing so that coloured
        cell values do not shift the byte positions of the '|' separators
        relative to where they appear in the uncoloured header row.
        """

        data = []
        separators: Optional[List[int]] = None
        names: Optional[List[str]] = None
        row_idx = 0

        for raw_line in table.decode("utf-8").split("\n"):
            # Strip ANSI colour codes so that byte positions equal visual
            # positions on every row, matching the uncoloured header row.
            line = re.sub(r'\x1b\[[0-9;]*m', '', raw_line).strip()
            if not line:
                continue
            assert line[0] == "|" and line[-1] == "|"

            if row_idx == 0:
                # Header row: locate every '|' to establish fixed column
                # boundaries that will be reused for all data rows.
                separators = [i for i, ch in enumerate(line) if ch == "|"]
                names = [
                    line[separators[i] + 1 : separators[i + 1]].strip()
                    for i in range(len(separators) - 1)
                ]
            elif row_idx > 1:
                # Data row: extract each cell by slicing between the boundary
                # positions fixed by the header, not by splitting on '|'.
                values = [
                    line[separators[i] + 1 : separators[i + 1]].strip()
                    for i in range(len(separators) - 1)
                ]
                values = [None if not v else v for v in values]
                data.append(dict(zip(names, values)))
            # row_idx == 1 is the divider bar (---|---...) and is skipped.

            row_idx += 1

        return data

    @staticmethod
    def parse_raw_json(json: bytes) -> List[Dict[str, Any]]:
        """
        parse raw json blocks into list of dicts
        """

        data = []

        for line in json.decode("utf-8").split("\n"):
            line = line.strip()
            if len(line) == 0:
                continue
            data.append(loads(line))

        return data

    @classmethod
    def parse_ls_pools(cls, raw: bytes, json: bool = False) -> List[ApoolDescription]:
        """
        parse output of `abgleich ls` for list of pools
        """

        data = cls.parse_raw_json(raw) if json else cls.parse_raw_table(raw)
        return [ApoolDescription(**entry) for entry in data]

    @classmethod
    def parse_ls_tree(cls, raw: bytes, json: bool = False) -> List[EntryDescription]:
        """
        parse output of `abgleich ls` for list of contents of pool
        """

        data = cls.parse_raw_json(raw) if json else cls.parse_raw_table(raw)
        return [EntryDescription.from_row(row, json=json) for row in data]

    @classmethod
    def parse_transactions(cls, raw: bytes, json: bool = False) -> List[Transaction]:
        """
        parse output of `abgleich` for list of transactions
        """

        # transactions are always followed by a json-block indicating automatic yes
        raw = raw.split(b'{"run":true}\n')[0]

        data = cls.parse_raw_json(raw) if json else cls.parse_raw_table(raw)
        return [Transaction.from_fields(**entry) for entry in data]

    def _print_test_close(self, *args: str, res: Result, width: int):
        """
        print meta data resulting from running abgleich
        """

        print(colored('-' * width, color = "dark_grey"))

        for msg in res.stderr2logs().msgs:
            if msg.level <= logging.DEBUG:
                color, attrs = "dark_grey", None
            elif msg.level <= logging.INFO:
                color, attrs = "light_green", None
            else:
                color, attrs = "light_yellow", ["bold"]
            print((
                colored(f"{msg.idx:03d}", color = "dark_grey")
                + " "
                + colored(msg.raw.decode("utf-8"), color = color, attrs = attrs)
            ))

        print(colored('-' * width, color = "dark_grey"))

        if any(arg in args for arg in ("--help", "--version")):
            print(colored(res.stdout.decode("utf-8").rstrip(), color = "dark_grey"))
        else:
            print(res.stdout.decode("utf-8").rstrip())

        # print(colored('-' * width, color = "dark_grey"))

    @staticmethod
    def _print_test_open(*args: str, fragments: Tuple[str, ...], width: int):
        """
        print meta data about how abgleich will be running
        """

        print(colored('-' * width, color = "dark_grey"))

        print((
            colored("$", color = "blue")
            + " "
            + colored(join([NAME, *fragments, *args]), color = "light_blue", attrs = ["bold"])
        ))

    @staticmethod
    def _write_test_logs(*args: str, fragments: Tuple[str, ...], fn: str, res: Result):
        """
        write meta data resulting from running abgleich
        """

        if any(arg in args for arg in ("--help", "--version")):
            return

        with open(fn, mode = "w", encoding = "utf-8") as f:
            f.write(join([NAME, *fragments, *args]))
            f.write("\n")
            for msg in res.stdout2logs().msgs:
                f.write(msg.raw.decode("utf-8"))
                f.write("\n")

    def abgleich(
        self,
        subcommand: Subcmd,
        *args: str,
        stdin: Optional[bytes] = None,
        timeout: Optional[int] = None,
        env: Optional[Dict[str, str]] = None,
        background: bool = False,
        user: Optional[str] = None,
        host: Host = Host.localhost,
    ) -> Union[Result, Callable[[], Result]]:
        """
        run abgleich

        TODO options or env vars for debug vs. release builds
        """

        if not self._open:
            raise ValueError("context not open")

        fragments = tuple() if subcommand is Subcmd.none else (subcommand.to_cli(),)

        if config_is_verbose():
            self._print_test_open(*args, fragments = fragments, width = self._width)

        env_ = self._get_env(host = host, user = user, incl_os_env = True, os_env_matches = "^(PATH$|RUST)")
        if env is not None:
            env_.update(env)

        cmd = Command(*split(self.target), *fragments, *args).with_env(env = env_).with_user(name = user).on_host(host = host)

        if not background:
            res = cmd.run(
                stdin = stdin,
                timeout = timeout,
                cwd = self._nodes[host].root.value,
            )
            if config_is_verbose():
                self._print_test_close(*args, res = res, width = self._width)
            if config_log_to_disk():
                self._write_test_logs(
                    *args,
                    fragments = fragments,
                    fn = self._get_next_log_filename(),
                    res = res,
                )
            return res

        steps = cmd.run_background(
            stdin = stdin,
            timeout = timeout,
            cwd = self._nodes[host].root.value,
        )  # generator, two steps
        _ = next(steps)  # run stage one

        @typechecked
        def await_func() -> Result:
            res = next(steps)
            if config_is_verbose():
                self._print_test_close(*args, res = res, width = self._width)
            return res

        return await_func  # allow consumer to trigger stage two

    def close(self, force: bool = False):
        """
        destroy context and its resources
        """

        if not self._open and not force:
            raise ValueError("context not open")

        self._open = False

        for node in self._nodes.values():
            if not node.required:
                continue
            if node.host is Host.localhost:
                config_fn = node.root.join(CONFIG_FN)
                if config_fn.exists(node.host):
                    config_fn.unlink(node.host)
            node.close(force = force)

    def get_journal(self, minutes: int = 10, ignore_errors: bool = False, host: Host = Host.localhost) -> List[Dict]:
        """
        access journalctl and return matching logs
        """

        res = Command(
            "journalctl",
            "--output=json",
            "--since", f'{minutes:d}min ago',
            "--all",
        ).with_sudo().on_host(host).run()
        res.assert_exitcode(0)

        return res.stdout2dicts(ignore_errors = ignore_errors)

    def is_error_valid(self, msg: Msg, name: str, fragments: Optional[Dict[int, str]] = None, silent: bool = False) -> bool:
        """
        validate message to be anticipated error and correct code
        """

        if not self._open:
            raise ValueError("context not open")

        traceback = msg["traceback"].split(TRACEBACK_SEP)

        if traceback[0] != name:
            return False

        if fragments is None:
            return True

        for idx, fragment in fragments.items():
            if idx >= len(traceback):
                if not silent:
                    print(f"\ntraceback length mismatch, idx {idx:d}, expected {fragment:s}")
                return False
            if re.compile(fragment).match(traceback[idx]) is None:
                if not silent:
                    print(f"\ntraceback content mismatch, idx {idx:d}, expected {fragment:s}, observed {traceback[idx]:s}")
                return False

        return True

    def open(self):
        """
        create context and its resources
        """

        if self._open:
            raise ValueError("context already open")

        for node in self._nodes.values():
            if not node.required:
                continue
            node.open()
            if node.host is Host.localhost and self._testconfig["abgleich/configfile"]:
                node.root.join(CONFIG_FN).create_file(node.host, self.config.to_raw())

        self._open = True

    def reload(self):
        """
        reload zpools for validation
        """

        if not self._open:
            raise ValueError("context not open")

        for node in self._nodes.values():
            if not node.required:
                continue
            node.reload()

    def shell(self, prefix: str = "debug"):
        """
        launch interactive shell on node current-a from within test contexts on local node
        """

        if not self._open:
            raise ValueError("context not open")

        shell(
            prefix = prefix,
            cwd = self._nodes[Host.localhost].root.value,
            target = self.target,
            hostnames = [host.to_host_name() for host in self._nodes.keys() if host is not Host.localhost],
            proc_env = self._get_env(host = Host.localhost, incl_os_env = False),
            os_env = self._get_os_env(host = Host.localhost),
        )
