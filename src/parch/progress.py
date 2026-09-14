"""Stdlib logging → one-line TTY bar for ``parch press``. Quiet off a TTY."""

import logging
import sys
from typing import TextIO

LOGGER_NAME = "parch.progress"
CURRENT_ATTR = "progress_current"
TOTAL_ATTR = "progress_total"
KIND_ATTR = "progress_kind"

_BAR_WIDTH = 10

log = logging.getLogger(LOGGER_NAME)


class ProgressRecordFilter(logging.Filter):
    """Keep records that carry structured page-progress extras."""

    def filter(self, record: logging.LogRecord) -> bool:
        return (
            getattr(record, CURRENT_ATTR, None) is not None
            and getattr(record, TOTAL_ATTR, None) is not None
            and getattr(record, KIND_ATTR, None) is not None
        )


class ProgressBarHandler(logging.Handler):
    """Draw ``parch |████░░░░░░| 4/10  cover`` on stderr from progress records."""

    def __init__(self, stream: TextIO | None = None) -> None:
        super().__init__()
        self.stream = sys.stderr if stream is None else stream
        self.addFilter(ProgressRecordFilter())

    def emit(self, record: logging.LogRecord) -> None:
        try:
            if not self.stream.isatty():
                return
            current = int(getattr(record, CURRENT_ATTR))
            total = int(getattr(record, TOTAL_ATTR))
            kind = str(getattr(record, KIND_ATTR))
            filled = (
                0 if total <= 0 else min(_BAR_WIDTH, (current * _BAR_WIDTH) // total)
            )
            bar = f"{'█' * filled}{'░' * (_BAR_WIDTH - filled)}"
            ending = "\n" if total > 0 and current >= total else ""
            self.stream.write(f"\rparch |{bar}| {current}/{total}  {kind}{ending}")
            self.stream.flush()
        except Exception:
            self.handleError(record)


def install_progress_bar(stream: TextIO | None = None) -> ProgressBarHandler:
    """Attach ``ProgressBarHandler`` to ``parch.progress``; do not propagate."""
    handler = ProgressBarHandler(stream)
    log.addHandler(handler)
    log.setLevel(logging.INFO)
    log.propagate = False
    return handler


def remove_progress_bar(handler: ProgressBarHandler) -> None:
    """Detach a handler installed by ``install_progress_bar``."""
    log.removeHandler(handler)
    handler.close()
    if not log.handlers:
        log.propagate = True
        log.setLevel(logging.NOTSET)
