import os
from shlex import quote
import sys
from tempfile import NamedTemporaryFile
from typing import Dict, Optional

from termcolor import colored

from ._command import Command
from ._const import NAME


def shell(
    prefix: str,
    cwd: str,
    target: str,
    hostnames: list[str],
    proc_env: Optional[Dict[str, str]] = None,  # for abgleich
    os_env: Optional[Dict[str, str]] = None,  # for bashrc
):
    """
    launch interactive shell from within test contexts, assumes bash
    """

    bashrc = ""
    fn = os.path.join(os.path.expanduser("~"), ".bashrc")
    if os.path.exists(fn):
        with open(fn, mode = "r", encoding = "utf-8") as f:
            bashrc = f.read()

    variables = []
    if os_env is not None:
        for name, value in os_env.items():
            variables.append(f"{name:s}={quote(value):s}")

    full_prefix = colored(
        f'[{NAME:s} {prefix:s}]',
        color = "red",
        attrs = ["bold"],
    )
    # TODO add variables to bashrc here
    variables.append("_PS1PREFIX=" + quote(full_prefix))
    variables.append(
        'PS1="$_PS1PREFIX ${PS1:-}"'
    )

    prefix = ""
    if proc_env is not None:
        env_vars = []
        for name, value in proc_env.items():
            env_vars.append(f"{name:s}=" + quote(value))
        prefix = " ".join(env_vars) + " "

    funcs = f"""
    {NAME:s} () {{
        {prefix:s}{target:s} $@
    }}
    """  # TODO add functions to bashrc here

    sys.stdout.write("\n")
    sys.stdout.write(full_prefix + " " + colored("<START>", color = "red", attrs = ["bold"]) + "\n")
    sys.stdout.write(full_prefix + " " + colored(f"`{NAME:s}` is linked to `{target:s}` and accepts arguments as well as pipes.", color = "dark_grey") + "\n")
    sys.stdout.write(full_prefix + " " + colored("Other test nodes reachable via ssh: " + ", ".join(hostnames)) + "\n")
    sys.stdout.write(full_prefix + " " + colored("Leave with `exit` ...", color = "dark_grey") + "\n")
    sys.stdout.flush()

    with NamedTemporaryFile() as file:

        file.write("\n".join([
            bashrc,
            *variables,
            funcs,
            f"cd {quote(cwd):s}",
        ]).encode("utf-8"))
        file.flush()

        os.chmod(file.name, 0o0666)  # for non-root users

        cmd = Command("bash", "--rcfile", file.name, "-i")
        _ = cmd.run(capture_stdout = False, capture_stderr = False, interactive = True)

    sys.stdout.write(full_prefix + " " + colored("<STOP>", color = "red", attrs = ["bold"]) + "\n")
    sys.stdout.flush()
