"""Press progress: TTY bar + optional file. Stdlib only; dual sink."""

import json
import os
import sys
from pathlib import Path

_BAR_WIDTH = 10
PROGRESS_FILE_ENV = "PARCH_PROGRESS_FILE"


def resolve_progress_file(explicit: str | Path | None = None) -> Path | None:
    """``--progress-file`` wins; else ``PARCH_PROGRESS_FILE``. Empty is unset."""
    token = explicit if explicit is not None else os.environ.get(PROGRESS_FILE_ENV)
    if token is None or token == "":
        return None
    return Path(token)


def format_bar(i: int, n: int, kind: str) -> str:
    filled = 0 if n <= 0 else min(_BAR_WIDTH, (i * _BAR_WIDTH) // n)
    bar = f"{'█' * filled}{'░' * (_BAR_WIDTH - filled)}"
    return f"parch |{bar}| {i}/{n}  {kind}"


def write_tty_bar(i: int, n: int, kind: str) -> None:
    """Redraw ``parch |████░░░░░░| 4/10  cover`` on stderr when it is a TTY."""
    stream = sys.stderr
    if not stream.isatty():
        return
    ending = "\n" if n > 0 and i >= n else ""
    stream.write(f"\r{format_bar(i, n, kind)}{ending}")
    stream.flush()


def write_progress_line(path: Path, i: int, n: int, kind: str) -> None:
    """Append one JSONL record: ``{"i":4,"n":10,"kind":"cover"}``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    record = json.dumps({"i": i, "n": n, "kind": kind}, separators=(",", ":"))
    with path.open("a", encoding="utf-8") as fh:
        fh.write(record + "\n")


class ProgressReport:
    """Same tick updates the TTY bar (if TTY) and optionally a progress file."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf-8")

    def __call__(self, i: int, n: int, kind: str) -> None:
        write_tty_bar(i, n, kind)
        if self.path is not None:
            write_progress_line(self.path, i, n, kind)


def report_progress(
    i: int,
    n: int,
    kind: str,
    *,
    progress_file: Path | None = None,
) -> None:
    """Dual sink: TTY bar when stderr is a TTY; JSONL line when a file is set."""
    write_tty_bar(i, n, kind)
    if progress_file is not None:
        write_progress_line(progress_file, i, n, kind)
