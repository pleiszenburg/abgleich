from datetime import datetime
from json import dumps, loads
from typing import Any, Dict, Iterator, Optional

from typeguard import typechecked

import logging
from ._errors import OutputParserError


@typechecked
class Msg:
    """
    wrapper around tracing log message
    """

    def __init__(
        self,
        timestamp: datetime,
        level: int,
        fields: Dict[str, Any],
        target: str,
        stream: str,
        idx: int,
        raw: bytes,
    ):
        """
        init
        """

        self._timestamp = timestamp
        self._level = level
        self._fields = fields
        self._target = target
        self._stream = stream
        self._idx = idx
        self._raw = raw

    def __repr__(self) -> str:
        """
        interactive presentation
        """

        return (
            "<Msg "
            f"timestamp={self._timestamp.isoformat():s} "
            f"level={self._level:d} "
            f"target={self._target:s} "
            f"stream={self._stream:s} "
            f"idx={self._idx:d} "
            f"fields={dumps(self._fields):s}>"
        )

    def __getitem__(self, name: str) -> Any:
        """
        field by name
        """

        return self._fields[name]

    @property
    def idx(self) -> int:
        """
        line number
        """

        return self._idx

    @property
    def timestamp(self) -> datetime:
        """
        time stamp
        """

        return self._timestamp

    @property
    def level(self) -> int:
        """
        log level
        """

        return self._level

    @property
    def raw(self) -> bytes:
        """
        original message
        """

        return self._raw

    @property
    def stream(self) -> str:
        """
        std stream
        """

        return self._stream

    @property
    def target(self) -> str:
        """
        log target
        """

        return self._target

    def keys(self) -> Iterator[str]:
        """
        all field names
        """

        return (name for name in self._fields.keys())

    def matches(self,
        timestamp: Optional[datetime] = None,
        level: Optional[int] = None,
        fields: Optional[Dict[str, Any]] = None,
        target: Optional[str] = None,
        stream: Optional[str] = None,
        idx: Optional[int] = None,
    ):
        """
        matches against selected fields
        """

        return not any((
            timestamp is not None and self._timestamp != timestamp,
            level is not None and self._level != level,
            fields is not None and self._fields != fields,
            timestamp is not None and self._target != target,
            stream is not None and self._stream != stream,
            idx is not None and self._idx != idx
        ))

    @staticmethod
    def _level2int(level: str) -> int:
        """
        translate logging levels
        """

        if level == "TRACE":
            return 0

        return {
            name: getattr(logging, name)
            for name in (
                "INFO",
                "DEBUG",
                "WARN",
                "ERROR",
                "CRITICAL",
            )
        }[level]

    @classmethod
    def from_line(cls, line: bytes, stream: str, idx: int):
        """
        process raw output line
        """

        try:
            msg = loads(line)
        except Exception as e:
            raise OutputParserError(f"line {idx:d} on {stream:s}", line) from e

        assert msg["timestamp"][-1].upper() == "Z"

        return cls(
            timestamp = datetime.fromisoformat(msg["timestamp"][:-1]),
            level = cls._level2int(msg["level"]),
            fields = msg["fields"],
            target = msg["target"],
            stream = stream,
            idx = idx,
            raw = line,
        )
