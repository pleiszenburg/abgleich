from subprocess import Popen, PIPE


TEMPLATE = """.. _cli:

.. DO NOT MANUALLY EDIT THIS FILE! IT IS OVERWRITTEN FOR EACH BUILD BY `update_cli.py`.

CLI
===

The command line interface (CLI).

"""

HEADING_UNDERLINE = "-"


def get_help(*args: str) -> str:
    proc = Popen(["cargo", "run", "-q", "--", *args, "--help"], stdout = PIPE)
    out, _ = proc.communicate()
    return out.decode("utf-8").strip(" \t\n")


def parse_subcommands(description: str) -> list[str]:
    block = description.split("Commands:")[1].split("Options:")[0].strip(" \t\n")
    subcomands = []
    for line in block.splitlines():
        line = line.strip(" \t")
        if len(line) == 0:
            continue
        subcommand = line.split(" ")[0]
        if subcommand in ("help", "version"):
            continue
        subcomands.append(subcommand)
    return subcomands


def underline(line: str) -> str:
    assert "\n" not in line
    return line + "\n" + HEADING_UNDERLINE * len(line)


def literal(text: str) -> str:
    return ".. code:: text\n\n" + "\n".join((f"    {line:s}" for line in text.split("\n")))


def main():
    command_help = get_help()
    subcommands = parse_subcommands(command_help)
    output = [
        TEMPLATE,
        underline("``abgleich``"),
        2 * "\n",
        literal(command_help),
        2 * "\n",
    ]
    for subcommand in subcommands:
        command_help = get_help(subcommand)
        output.extend((
            underline(f"``abgleich {subcommand:s}``"),
            2 * "\n",
            literal(command_help),
            2 * "\n",
        ))
    with open("docs/source/cli.rst", mode = "w", encoding = "utf-8") as f:
        f.write("".join(output))


if __name__ == "__main__":
    main()
