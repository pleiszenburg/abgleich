from dataclasses import dataclass
from datetime import datetime
import re
from typing import Callable, Optional

from typeguard import typechecked


@dataclass(frozen=True)
class Spec:
    """
    describes a single-char chrono format specifier:
    its regex pattern, and — for datetime-carrying specifiers — the target
    field base name and a converter from matched string to (field_name, int_value)
    """

    regex: str
    base: Optional[str] = None
    conv: Optional[Callable[[str], tuple]] = None


# single-char chrono specifiers; specifiers without base/conv don't carry datetime info
_SPECS: dict[str, Spec] = {
    "Y": Spec(r"\d{4}",            "year",   lambda s: ("year",        int(s))),
    "C": Spec(r"\d{2}"),
    "y": Spec(r"\d{2}",            "year",   lambda s: ("year",        int(s) + 2000)),
    "m": Spec(r"\d{2}",            "month",  lambda s: ("month",       int(s))),
    "b": Spec(r"[A-Za-z]{3}"),
    "h": Spec(r"[A-Za-z]{3}"),
    "B": Spec(r"[A-Za-z]+"),
    "d": Spec(r"\d{2}",            "day",    lambda s: ("day",         int(s))),
    "e": Spec(r"[\d ]\d",          "day",    lambda s: ("day",         int(s.strip()))),
    "a": Spec(r"[A-Za-z]{3}"),
    "A": Spec(r"[A-Za-z]+"),
    "w": Spec(r"\d"),
    "u": Spec(r"\d"),
    "U": Spec(r"\d{2}"),
    "W": Spec(r"\d{2}"),
    "G": Spec(r"\d{4}"),
    "g": Spec(r"\d{2}"),
    "V": Spec(r"\d{2}"),
    "j": Spec(r"\d{3}"),
    "H": Spec(r"\d{2}",            "hour",   lambda s: ("hour",        int(s))),
    "k": Spec(r"[\d ]\d",          "hour",   lambda s: ("hour",        int(s.strip()))),
    "I": Spec(r"\d{2}"),
    "l": Spec(r"[\d ]\d"),
    "P": Spec(r"[ap]m"),
    "p": Spec(r"[AP]M"),
    "M": Spec(r"\d{2}",            "minute", lambda s: ("minute",      int(s))),
    "S": Spec(r"\d{2}",            "second", lambda s: ("second",      int(s))),
    "f": Spec(r"\d{9}",            "us",     lambda s: ("microsecond", int(s) // 1000)),
    "R": Spec(r"\d{2}:\d{2}"),
    "T": Spec(r"\d{2}:\d{2}:\d{2}"),
    "X": Spec(r".+"),
    "r": Spec(r".+"),
    "Z": Spec(r"\S+"),
    "z": Spec(r"[+-]\d{4}"),
    "c": Spec(r".+"),
    "+": Spec(r".+"),
    "s": Spec(r"-?\d+"),
    "t": Spec(r"\t"),
    "n": Spec(r"\n"),
    "%": Spec(r"%"),
}


@typechecked
class SnapshotFormat:
    """
    parses and generates snapshot names,
    identically to what abgleich's implementation based on chrono does
    """

    DEFAULT = r"abgleich_%Y-%m-%dT%H:%M:%S:%3f_backup"

    @classmethod
    def _chrono_to_named_regex(cls, fmt: str) -> tuple[str, list]:
        """
        convert a chrono-compatible format string to a regex with named capture
        groups for datetime-carrying specifiers; returns
        (pattern, [(group_name, converter)])
        where converter: str -> (datetime_field_name, int_value)
        """

        pattern = ""
        converters: list = []
        counts: dict[str, int] = {}

        def add(base: str, regex: str, conv) -> str:
            n = counts.get(base, 0)
            counts[base] = n + 1
            name = base if n == 0 else f"{base}_{n}"  # unique group name per base
            converters.append((name, conv))
            return f"(?P<{name}>{regex})"  # named capture group

        i = 0
        while i < len(fmt):
            c = fmt[i]
            if c != "%":
                pattern += re.escape(c)  # literal character
                i += 1
                continue
            if i + 1 >= len(fmt):
                pattern += re.escape("%")  # trailing lone %
                i += 1
                continue
            next_c = fmt[i + 1]
            if next_c == ":":
                if i + 2 < len(fmt) and fmt[i + 2] == ":":
                    pattern += r"[+-]\d{2}:\d{2}:\d{2}"  # %::z, seconds-precision offset
                    i += 4
                else:
                    pattern += r"[+-]\d{2}:\d{2}"  # %:z, minutes-precision offset
                    i += 3
            elif next_c == "#":
                pattern += r"[+-]\d{2}(?::\d{2}(?::\d{2})?)?"  # %#z, variable-precision offset
                i += 3
            elif next_c == ".":
                if i + 2 < len(fmt) and fmt[i + 2] in "369" and i + 3 < len(fmt) and fmt[i + 3] == "f":
                    n = int(fmt[i + 2])
                    regex = rf"\.\d{{{n}}}"  # dot-prefixed, fixed-width fractional seconds
                    conv = (
                        (lambda s: ("microsecond", int(s[1:]) * 1000)) if n == 3 else  # ms -> us
                        (lambda s: ("microsecond", int(s[1:])))         if n == 6 else  # us
                        (lambda s: ("microsecond", int(s[1:]) // 1000))                 # ns -> us
                    )
                    pattern += add("us", regex, conv)
                    i += 4  # %.3f / %.6f / %.9f
                elif i + 2 < len(fmt) and fmt[i + 2] == "f":
                    pattern += add("us", r"\.\d+", lambda s: ("microsecond", int(s[1:].ljust(9, "0")) // 1000))
                    i += 3  # %.f, variable-width, pad to ns then convert
                else:
                    pattern += re.escape("%.")  # unrecognised, treat as literal
                    i += 2
            elif next_c in "369" and i + 2 < len(fmt) and fmt[i + 2] == "f":
                n = int(next_c)
                regex = rf"\d{{{n}}}"  # fixed-width fractional seconds, no dot
                conv = (
                    (lambda s: ("microsecond", int(s) * 1000)) if n == 3 else  # ms -> us
                    (lambda s: ("microsecond", int(s)))         if n == 6 else  # us
                    (lambda s: ("microsecond", int(s) // 1000))                 # ns -> us
                )
                pattern += add("us", regex, conv)
                i += 3  # %3f / %6f / %9f
            elif next_c in _SPECS:
                spec = _SPECS[next_c]
                if spec.base is not None:
                    pattern += add(spec.base, spec.regex, spec.conv)  # datetime-carrying: named group
                else:
                    pattern += spec.regex  # non-datetime: plain pattern
                i += 2
            else:
                pattern += re.escape(fmt[i:i + 2])  # unknown specifier, treat as literal
                i += 2

        return pattern, converters

    @classmethod
    def _chrono_to_str(cls, fmt: str, dt: datetime) -> str:
        """
        format a datetime using a chrono-compatible format string;
        handles chrono-specific specifiers that differ from Python strftime
        """

        _SPECIAL = {  # specifiers that don't map directly to Python strftime
            "C": lambda d: f"{d.year // 100:02d}",       # century
            "e": lambda d: f"{d.day:2d}",                 # space-padded day
            "h": lambda d: d.strftime("%b"),               # alias for %b
            "k": lambda d: f"{d.hour:2d}",                # space-padded 24 h
            "l": lambda d: f"{d.hour % 12 or 12:2d}",    # space-padded 12 h
            "P": lambda d: d.strftime("%p").lower(),       # lowercase am/pm
            "f": lambda d: f"{d.microsecond * 1000:09d}", # nanoseconds (chrono %f != Python %f)
            "s": lambda d: str(int(d.timestamp())),        # unix timestamp
            "t": lambda d: "\t",
            "n": lambda d: "\n",
            "%": lambda d: "%",
            "+": lambda d: d.isoformat(),                  # RFC 3339
        }

        result = ""
        i = 0
        while i < len(fmt):
            c = fmt[i]
            if c != "%":
                result += c  # literal character
                i += 1
                continue
            if i + 1 >= len(fmt):
                result += "%"  # trailing lone %
                i += 1
                continue
            next_c = fmt[i + 1]
            if next_c == ":":
                if i + 2 < len(fmt) and fmt[i + 2] == ":":
                    tz = dt.strftime("%z")
                    result += f"{tz[:3]}:{tz[3:5]}:{tz[5:] or '00'}" if tz else ""  # %::z
                    i += 4
                else:
                    tz = dt.strftime("%z")
                    result += f"{tz[:3]}:{tz[3:]}" if tz else ""  # %:z
                    i += 3
            elif next_c == "#":
                result += dt.strftime("%z")  # %#z, raw offset
                i += 3
            elif next_c == ".":
                if i + 2 < len(fmt) and fmt[i + 2] in "369" and i + 3 < len(fmt) and fmt[i + 3] == "f":
                    n = int(fmt[i + 2])
                    us = dt.microsecond
                    result += f".{us // 1000:03d}" if n == 3 else f".{us:06d}" if n == 6 else f".{us * 1000:09d}"
                    i += 4  # %.3f / %.6f / %.9f, dot-prefixed
                elif i + 2 < len(fmt) and fmt[i + 2] == "f":
                    ns = dt.microsecond * 1000
                    result += "." + f"{ns:09d}".rstrip("0") or ".0"  # %.f, minimal digits
                    i += 3
                else:
                    result += "%."  # unrecognised, emit literally
                    i += 2
            elif next_c in "369" and i + 2 < len(fmt) and fmt[i + 2] == "f":
                n = int(next_c)
                us = dt.microsecond
                result += f"{us // 1000:03d}" if n == 3 else f"{us:06d}" if n == 6 else f"{us * 1000:09d}"
                i += 3  # %3f / %6f / %9f, no dot
            elif next_c in _SPECIAL:
                result += _SPECIAL[next_c](dt)  # chrono-specific handler
                i += 2
            elif next_c in _SPECS:
                result += dt.strftime(f"%{next_c}")  # delegate to Python strftime
                i += 2
            else:
                result += f"%{next_c}"  # unknown specifier, emit literally
                i += 2
        return result

    @classmethod
    def format_(cls, dt: datetime, format_: Optional[str] = None) -> str:
        """
        generate a snapshot name from a chrono-compatible format string and a datetime
        """

        if format_ is None:
            format_ = cls.DEFAULT

        return cls._chrono_to_str(format_, dt)

    @classmethod
    def parse(cls, name: str, format_: Optional[str] = None) -> datetime:
        """
        extract a datetime from a snapshot name given a chrono-compatible format string;
        assumes the format string carries at least year, month, and day
        """

        if format_ is None:
            format_ = cls.DEFAULT

        pattern, converters = cls._chrono_to_named_regex(format_)
        m = re.fullmatch(pattern, name)
        if m is None:
            raise ValueError(f"name {name!r} does not match format {format_!r}")
        fields: dict = {
            "year": 1970, "month": 1, "day": 1,
            "hour": 0, "minute": 0, "second": 0, "microsecond": 0,
        }
        for group_name, conv in converters:
            field, value = conv(m.group(group_name))
            fields[field] = value
        return datetime(**fields)

    @classmethod
    def match(cls, name: str, format_: Optional[str] = None) -> bool:
        """
        converts chrono format specifiers to regex fragments,
        checks if name was plausibly generated from format string
        """

        if format_ is None:
            format_ = cls.DEFAULT

        return bool(re.fullmatch(cls._chrono_to_named_regex(format_)[0], name))
