from datetime import datetime
from enum import Enum
import os
from typing import Any, Dict, Iterator

from typeguard import typechecked

from ._config import Config
from ._const import (
    DEFAULT_TARGET,
    VAR_LOG_TO_DISK,
    VAR_RELEASE,
    VAR_TARGET,
    VAR_VERBOSE,
)
from ._repr import repr_tree


@typechecked
def config_is_verbose() -> bool:
    """
    check if running in verbose mode
    """

    return bool(int(os.getenv(VAR_VERBOSE, "0")))


@typechecked
def config_log_to_disk() -> bool:
    """
    check if logs should be written to disk
    """

    return bool(int(os.getenv(VAR_LOG_TO_DISK, "0")))


@typechecked
def config_release() -> bool:
    """
    debug or release builds
    """

    return bool(int(os.getenv(VAR_RELEASE, "0")))


@typechecked
def config_target() -> str:
    """
    compiler & test target
    """

    return os.getenv(VAR_TARGET, DEFAULT_TARGET)


@typechecked
class TestConfig:
    """
    holds test context configuration
    """

    __test__ = False  # prevent collection as test case by pytest

    _DEFAULTS = {
        "abgleich": Config(),  # default config, no groups, no routes
        "abgleich/configfile": True,  # write config to file in expected location
        "abgleich/loglevel": 10,  # debug (0: tracing, 10: debug, 20: info i.e. normal operation)
        "nodes/current_a/required": True,  # node required, session setup
        "nodes/current_a/root": "/tmp/session",  # root folder of test session
        "nodes/current_a/zpools": [],  # list of zpools
        "nodes/current_b/required": False,  # node required, session setup
        "nodes/current_b/root": "/tmp/session",  # root folder of test session
        "nodes/current_b/zpools": [],  # list of zpools
        "nodes/other_a/required": False,  # node required, session setup
        "nodes/other_a/root": "/tmp/session",  # root folder of test session
        "nodes/other_a/zpools": [],  # list of zpools
        "nodes/other_b/required": False,  # node required, session setup
        "nodes/other_b/root": "/tmp/session",  # root folder of test session
        "nodes/other_b/zpools": [],  # list of zpools
    }

    def __init__(self, **kwargs):
        """
        builds configuration
        """

        kwargs = self._flatten(kwargs)

        if "nodes/current_a/required" in kwargs.keys() and not kwargs["nodes/current_a/required"]:
            raise ValueError("current_a runs the test suite and is therefore required")

        if "zpools" in kwargs.keys():
            if "nodes/current_a/zpools" in kwargs.keys():
                raise ValueError("zpools on current_a specified twice")
            kwargs["nodes/current_a/zpools"] = kwargs.pop("zpools")

        for key in kwargs.keys():
            if key not in self._DEFAULTS.keys():
                raise ValueError("unknown configuration parameter", key)

        self._custom = kwargs

    def __repr__(self) -> str:
        """
        config representation
        """

        custom = self._custom.copy()

        return repr_tree(
            base = "<TestConfig>",
            branches = custom,
        )

    def __getitem__(self, key: str) -> Any:
        """
        retrieve value
        """

        if key not in self._DEFAULTS.keys():
            raise ValueError("unknown configuration parameter", key)

        value = os.environ.get(self._to_env_name(key), None)
        if value is not None:
            if isinstance(self._DEFAULTS[key], datetime):
                return datetime.fromisoformat(value)
            if value.isdecimal():  # TODO only positive ints
                return int(value)
            if isinstance(self._DEFAULTS[key], Enum):
                return getattr(type(self._DEFAULTS[key]), value)
            return value

        try:
            return self._custom[key]
        except KeyError:
            pass

        return self._DEFAULTS[key]

    @property
    def nodes(self) -> Iterator[str]:
        """
        exposes all nodes by name
        """

        names = {
            key.split("/")[1]
            for key in self._DEFAULTS.keys()
            if key.startswith("nodes/")
        }
        return (name for name in names)

    @staticmethod
    def _to_env_name(key: str) -> str:
        """
        convert key to environment variable name
        """

        return f'{key.replace("/", "_").upper():s}'

    @classmethod
    def _flatten(cls, old: Dict) -> Dict:
        """
        flatten tree of dicts
        """

        new = dict()
        for okey, ovalue in old.items():
            if isinstance(ovalue, dict):
                unwrapped = cls._flatten(ovalue)
                for ukey, uvalue in unwrapped.items():
                    new[f"{okey:s}/{ukey:s}"] = uvalue
            else:
                new[okey] = ovalue
        return new
