"""One-line TTY progress bar for ``parch press``. Stdlib only; quiet off a TTY."""

import sys

_BAR_WIDTH = 10
_last_width = 0
_last_filled: int | None = None


def render_progress(i: int, n: int, label: str) -> None:
    """Redraw ``parch |████░░░░░░| 4/10  cover`` on stderr when it is a TTY.

    Space-pads to the previous frame width so a shorter label does not
    leave a leftover tail after ``\\r``. Write+flush only when the filled
    bar cell changes, or on the final page — skip other ticks.
    """
    global _last_filled, _last_width
    stream = sys.stderr
    if not stream.isatty():
        return
    filled = 0 if n <= 0 else min(_BAR_WIDTH, (i * _BAR_WIDTH) // n)
    done = n > 0 and i >= n
    if not done and _last_filled == filled:
        return
    bar = f"{'█' * filled}{'░' * (_BAR_WIDTH - filled)}"
    frame = f"parch |{bar}| {i}/{n}  {label}"
    padded = frame.ljust(_last_width)
    stream.write(f"\r{padded}{'\n' if done else ''}")
    stream.flush()
    if done:
        _last_filled = None
        _last_width = 0
    else:
        _last_filled = filled
        _last_width = len(padded)
