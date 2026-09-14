"""Stderr progress bar for ``parch press``. Stdlib only; quiet when not a TTY."""

import sys
from collections.abc import Callable
from typing import TextIO

BAR_WIDTH = 10
FILLED = "█"
EMPTY = "░"

type ProgressSink = Callable[[int, int, str], None]


def format_bar(current: int, total: int, kind: str, *, width: int = BAR_WIDTH) -> str:
    """``parch |████░░░░░░| 4/10  cover`` — █ filled, ░ empty, kind label."""
    if total > 0:
        filled = min(width, max(0, current * width // total))
    else:
        filled = 0
    body = f"{FILLED * filled}{EMPTY * (width - filled)}"
    label = f"  {kind}" if kind else ""
    return f"parch |{body}| {current}/{total}{label}"


class TtyProgress:
    """Rewrite one stderr line with ``\\r``. No-op when the stream is not a TTY."""

    def __init__(self, stream: TextIO | None = None) -> None:
        self._stream = sys.stderr if stream is None else stream
        self.enabled = self._stream.isatty()
        self._dirty = False

    def __call__(self, current: int, total: int, kind: str) -> None:
        if not self.enabled:
            return
        self._stream.write(f"\r{format_bar(current, total, kind)}")
        self._stream.flush()
        self._dirty = True
        if total > 0 and current >= total:
            self.close()

    def close(self) -> None:
        if self.enabled and self._dirty:
            self._stream.write("\n")
            self._stream.flush()
            self._dirty = False
