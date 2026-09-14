"""Press progress: a list of callables that plot notifies. Stdlib bar for the CLI."""

import sys
from collections.abc import Callable

type ProgressListener = Callable[[int, int, str], None]

_BAR_WIDTH = 10


class PressSession:
    """Mutable observer sink. Not a Protocol — just a list of callables."""

    def __init__(self) -> None:
        self.listeners: list[ProgressListener] = []

    def notify(self, i: int, n: int, label: str) -> None:
        for listener in list(self.listeners):
            listener(i, n, label)


session = PressSession()
listeners = session.listeners


def notify(i: int, n: int, label: str) -> None:
    """Fan out a page tick to every registered listener."""
    session.notify(i, n, label)


def render_progress(i: int, n: int, label: str) -> None:
    """Redraw ``parch |████░░░░░░| 4/10  cover`` on stderr when it is a TTY."""
    stream = sys.stderr
    if not stream.isatty():
        return
    filled = 0 if n <= 0 else min(_BAR_WIDTH, (i * _BAR_WIDTH) // n)
    bar = f"{'█' * filled}{'░' * (_BAR_WIDTH - filled)}"
    ending = "\n" if n > 0 and i >= n else ""
    stream.write(f"\rparch |{bar}| {i}/{n}  {label}{ending}")
    stream.flush()
