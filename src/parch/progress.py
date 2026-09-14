"""Tiny press progress reporter. Shared stderr bar; not a framework."""

import sys
from typing import Protocol, TextIO

BAR_WIDTH = 10


class Progress(Protocol):
    """Reporter for a press/plot page loop. Three calls, nothing else."""

    def start(self, total: int) -> None:
        """Know the page count before the first ``advance``."""

    def advance(self, page: str) -> None:
        """One page finished. ``page`` is the dest (``cover``, …)."""

    def done(self) -> None:
        """Loop finished. TTY bars emit a trailing newline."""


def bar_line(current: int, total: int, page: str, *, width: int = BAR_WIDTH) -> str:
    """``parch |████░░░░░░| 4/10  cover`` — stdlib glyphs, no color."""
    if total <= 0:
        filled = 0
    else:
        filled = min(width, max(0, width * current // total))
    bar = f"{'█' * filled}{'░' * (width - filled)}"
    return f"parch |{bar}| {current}/{total}  {page}"


class NullProgress:
    """No-op reporter for tests and non-TTY streams."""

    def start(self, total: int) -> None:
        return

    def advance(self, page: str) -> None:
        return

    def done(self) -> None:
        return


class StderrBar:
    """``\\r`` bar on a TTY stream. Quiet when ``isatty()`` is false."""

    def __init__(self, stream: TextIO | None = None, *, width: int = BAR_WIDTH) -> None:
        self._stream = sys.stderr if stream is None else stream
        self._width = width
        self._total = 0
        self._current = 0
        self._last = 0

    def start(self, total: int) -> None:
        self._total = total
        self._current = 0
        self._paint("")

    def advance(self, page: str) -> None:
        self._current += 1
        self._paint(page)

    def done(self) -> None:
        if not self._live():
            return
        self._stream.write("\n")
        self._stream.flush()

    def _live(self) -> bool:
        isatty = getattr(self._stream, "isatty", None)
        return bool(isatty and isatty())

    def _paint(self, page: str) -> None:
        if not self._live():
            return
        line = bar_line(self._current, self._total, page, width=self._width)
        pad = max(0, self._last - len(line))
        self._stream.write(f"\r{line}{' ' * pad}")
        self._last = len(line)
        self._stream.flush()


def reporter_for(stream: TextIO | None = None) -> Progress:
    """StderrBar on a TTY; NullProgress otherwise."""
    out = sys.stderr if stream is None else stream
    isatty = getattr(out, "isatty", None)
    if isatty and isatty():
        return StderrBar(out)
    return NullProgress()
