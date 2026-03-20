from functools import wraps
from shutil import get_terminal_size
from traceback import print_exception
from typing import Any, Callable, Dict, List, Optional

import pytest
from termcolor import colored
from typeguard import typechecked

from ._context import Context
from ._repr import repr_tree
from ._testconfig import TestConfig, config_is_verbose
from ._threads import threads


@typechecked
def _clean_doc(doc: str) -> str:
    """
    clean up doc string
    """

    if len(doc.strip()) == 0:
        return ""

    lines = [line for line in doc.split("\n")]

    while len(lines) > 0:  # rstrip
        if len(lines[-1].strip()) == 0:
            lines.pop(-1)
        else:
            break
    while len(lines) > 0:  # lstrip
        if len(lines[0].strip()) == 0:
            lines.pop(0)
        else:
            break

    shortest = min(len(line) - len(line.lstrip(" ")) for line in lines)
    lines = [line[shortest:] for line in lines]  # lshift
    return "\n".join(lines)


@typechecked
def _center_headline(headline: str, sign: str, width: int, color: str, attrs: Optional[List[str]] = None):
    """
    centers a headline
    """

    center = len(headline)
    right = left = (width - center) // 2
    if width % 2 != 0:
        right -= 1

    print(colored(" " * left + sign * center + " " * right, color = color, attrs = attrs))
    print(colored(" " * left + headline + " " * right, color = color, attrs = attrs))
    print(colored(" " * left + sign * center + " " * right, color = color, attrs = attrs))


@typechecked
def _print_testheader(*args: Any, func: Callable, meta: Dict[str, Any], **kwargs: Any):
    """
    print meta data of current test
    """

    width = get_terminal_size().columns
    print("")  # empty line

    if not meta["header"]:
        print(colored('-' * width, color = "dark_grey"))
        _center_headline(
            headline = func.__name__,
            sign = "=",
            width = width,
            color = "light_cyan",
            attrs = ["bold"],
        )
        if hasattr(func, "__doc__"):  # can be missing
            doc = _clean_doc(func.__doc__)
            if len(doc) > 0:  # can be empty
                print(colored(doc, color = "light_cyan"))
        meta["header"] = True  # only print this part once

    meta["permutations"] += 1
    print(colored('-' * width, color = "dark_grey"))
    _center_headline(
        headline = f'{func.__name__:s}: permutation {meta["permutations"]:d}',
        sign = "-",
        width = width,
        color = "light_cyan",
    )
    assert len(args) == 0
    print(colored(repr_tree(
        base = "permutation",
        branches = kwargs,
    ), color = "dark_grey"))


@typechecked
class Environment:
    """
    convenience wrapper for injecting configured contexts into test functions
    """

    def __init__(self, *configs: TestConfig):
        """
        init
        """

        if len(configs) == 0:
            configs = (TestConfig(),)  # default

        self._configs = configs

    def __call__(self, func: Callable) -> Callable:
        """
        function decorator
        """

        meta = dict(header = False, permutations = 0)

        @pytest.mark.parametrize('ctx', self._configs)
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:

            try:
                if config_is_verbose():
                    _print_testheader(*args, func = func, meta = meta, **kwargs)
                context = Context(
                    testconfig = kwargs.pop("ctx"),
                )
                context.open()
            except Exception as infra_error:  # pylint: disable=W0718
                self._exit(infra_error)

            test_error = None
            try:
                ret = func(*args, ctx = context, **kwargs)
            except Exception as e:  # pylint: disable=W0718
                test_error = e

            try:
                context.close()
            except Exception as infra_error:  # pylint: disable=W0718
                self._exit(infra_error, test_error)

            if test_error is not None:
                raise test_error

            return ret

        return wrapper

    def _exit(self, infra_error: Exception, test_error: Optional[Exception] = None):
        """
        critical error in test infrastructure, stop test suite
        """

        print(colored("TEST INFRASTRUCTURE FAILED!", color = "red", attrs = ["bold"]))
        print_exception(infra_error)

        if test_error is not None:
            print(colored("TEST CASE WITHIN FAILED INFRASTRUCTURE ALSO FAILED!", color = "red", attrs = ["bold"]))
            print_exception(test_error)

        threads.clear()

        pytest.exit(str(infra_error), returncode = 1)
