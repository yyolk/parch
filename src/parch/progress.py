"""One-line TTY progress bar for ``parch press``. Stdlib only; quiet off a TTY."""

import sys

_BAR_WIDTH = 10
_last_width = 0


def render_progress(i: int, n: int, label: str) -> None:
    """Redraw ``parch |████░░░░░░| 4/10  cover`` on stderr when it is a TTY.

    Space-pads to the previous frame width so a shorter label does not
    leave a leftover tail after ``\\r``.
    """
    global _last_width
    stream = sys.stderr
    if not stream.isatty():
        return
    filled = 0 if n <= 0 else min(_BAR_WIDTH, (i * _BAR_WIDTH) // n)
    bar = f"{'█' * filled}{'░' * (_BAR_WIDTH - filled)}"
    frame = f"parch |{bar}| {i}/{n}  {label}"
    padded = frame.ljust(_last_width)
    done = n > 0 and i >= n
    stream.write(f"\r{padded}{'\n' if done else ''}")
    stream.flush()
    _last_width = 0 if done else len(padded)
