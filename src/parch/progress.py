"""Context-managed TTY progress bar for ``parch press``. Stdlib only; quiet off a TTY."""

import sys
from contextlib import contextmanager
from typing import TextIO

from parch.sections import Page

_BAR_WIDTH = 10


def _bar_line(current: int, total: int, label: str = "") -> str:
    filled = 0 if total <= 0 else min(_BAR_WIDTH, _BAR_WIDTH * current // total)
    bar = f"{'█' * filled}{'░' * (_BAR_WIDTH - filled)}"
    extra = f"  {label}" if label else ""
    return f"\rparch |{bar}| {current}/{total}{extra}"


@contextmanager
def page_progress(total: int, stream: TextIO | None = None):
    """Yield ``tick(i, page)`` or ``tick(page)``. ``with`` owns start and done.

    Start writes ``0/total`` on a TTY. Each ``tick`` rewrites the bar. Done
    always emits the trailing newline — including when the paint loop raises.
    Quiet when ``stream`` (default stderr) is not a TTY.
    """
    out = sys.stderr if stream is None else stream
    live = bool(getattr(out, "isatty", lambda: False)())
    current = 0

    def write(i: int, label: str = "") -> None:
        if not live:
            return
        out.write(_bar_line(i, total, label))
        out.flush()

    def tick(*args: int | Page) -> None:
        nonlocal current
        match args:
            case (page,):
                current += 1
                i = current
            case (i, page):
                if not isinstance(i, int):
                    raise TypeError("tick(i, page) needs int current")
                current = i
            case _:
                raise TypeError("tick(page) or tick(i, page)")
        if not isinstance(page, Page):
            raise TypeError("tick expects a Page")
        write(i, page.kind)

    write(0)
    try:
        yield tick
    finally:
        if live:
            out.write("\n")
            out.flush()
