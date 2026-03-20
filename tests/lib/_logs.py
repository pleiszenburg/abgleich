from typing import Iterable, List

import logging
from logging import INFO
from typeguard import typechecked

from ._const import NAME
from ._msg import Msg


@typechecked
class Logs:
    """
    parses and analyzes logged data
    """

    def __init__(self, stream: str, msgs: List[Msg]):
        """
        init
        """

        self._stream = stream
        self._msgs = msgs

    def __repr__(self):
        """
        interactive representation
        """

        return f"<Log stream={self._stream:s} msgs={len(self):d}>"

    def __len__(self) -> int:
        """
        number of messages
        """

        return len(self._msgs)

    def __getitem__(self, idx: int) -> Msg:
        """
        specific message in log
        """

        return self._msgs[idx]

    @property
    def msgs(self) -> Iterable[Msg]:
        """
        all messages
        """

        return (msg for msg in self._msgs)

    def filtered(self, min_level: int = INFO, target_prefix: str = NAME) -> Iterable[Msg]:
        """
        filter relevant messages
        """

        for msg in self._msgs:

            if msg.level < min_level:
                continue
            if not msg.target.startswith(target_prefix):
                continue

            yield msg

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
    def from_raw(cls, stream: str, raw: bytes, ignore_errors: bool = False):
        """
        from raw output bytes
        """

        msgs = []
        for idx, line in enumerate(raw.split(b"\n"), start = 1):
            if len(line.strip()) == 0:
                continue
            error = None
            try:
                msg = Msg.from_line(
                    line = line,
                    idx = idx,
                    stream = stream
                )
            except Exception as e:  # pylint: disable=W0718
                error = e
            if error is not None:
                if ignore_errors:
                    continue
                else:
                    raise error
            msgs.append(msg)

        return cls(stream = stream, msgs = msgs)
