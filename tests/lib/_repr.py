from typing import Any, Dict, List, Union

from typeguard import typechecked


HORIZONTAL = "━"
VERTICAL = "┃"
MIDDLE_BRANCH = "┣"
BOTTOM_BRANCH = "┗"


@typechecked
def repr_tree(
    base: str,  # base/parent object
    branches: Union[Dict[str, Any], List[Any]],
) -> str:
    """
    improved repr for tree structures
    """

    lines = [base]

    if isinstance(branches, dict):

        for idx, (name, branch) in enumerate(branches.items(), start = 1):

            last = idx >= len(branches)
            sign = (BOTTOM_BRANCH if last else MIDDLE_BRANCH) + HORIZONTAL
            fill = (" " if last else VERTICAL) + " "

            repr_branch = repr_tree(f"[{type(branch).__name__:s}]", branch) if any(
                isinstance(branch, type_) for type_ in (list, dict)
            ) else repr(branch)
            branch_lines = repr_branch.split("\n")
            lines.append(f"{sign:s}{name:s}={branch_lines[0]}")
            for branch_line in branch_lines[1:]:
                lines.append(f"{fill:s}{branch_line}")

    elif isinstance(branches, list):

        for idx, branch in enumerate(branches, start = 1):

            last = idx >= len(branches)
            sign = (BOTTOM_BRANCH if last else MIDDLE_BRANCH) + HORIZONTAL
            fill = (" " if last else VERTICAL) + " "

            branch_lines = repr(branch).split("\n")
            lines.append(f"{sign:s}{branch_lines[0]}")
            for branch_line in branch_lines[1:]:
                lines.append(f"{fill:s}{branch_line}")

    return "\n".join(lines)
