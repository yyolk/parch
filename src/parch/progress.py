"""One-line TTY progress bar for ``parch press``. Stdlib only; quiet off a TTY."""

import sys

_BAR_WIDTH = 10
_EL = "\033[K"


def render_progress(i: int, n: int, label: str) -> None:
    """Redraw ``parch |████░░░░░░| 4/10  cover`` on stderr when it is a TTY.

    Erases to end of line after each frame so a shorter label does not
    leave a leftover tail after ``\\r``.
    """
    stream = sys.stderr
    if not stream.isatty():
        return
    filled = 0 if n <= 0 else min(_BAR_WIDTH, (i * _BAR_WIDTH) // n)
    bar = f"{'█' * filled}{'░' * (_BAR_WIDTH - filled)}"
    frame = f"parch |{bar}| {i}/{n}  {label}"
    done = n > 0 and i >= n
    stream.write(f"\r{frame}{_EL}{'\n' if done else ''}")
    stream.flush()
