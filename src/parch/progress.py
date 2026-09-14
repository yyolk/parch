"""One-line TTY progress bar for ``parch press``. Stdlib only; quiet off a TTY."""

import sys

_BAR_WIDTH = 10


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
