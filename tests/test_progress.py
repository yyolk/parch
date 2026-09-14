import inspect
import logging
import sys

from parch.books import ProjectsNotebook, YearPlanner
from parch.plotter import RecordingPlotter
from parch.press import main, press
from parch.progress import (
    CURRENT_ATTR,
    KIND_ATTR,
    LOGGER_NAME,
    TOTAL_ATTR,
    ProgressBarHandler,
    ProgressRecordFilter,
    install_progress_bar,
    remove_progress_bar,
)
from parch.spec import Spec


class _TTY:
    def __init__(self) -> None:
        self.chunks: list[str] = []

    def isatty(self) -> bool:
        return True

    def write(self, text: str) -> int:
        self.chunks.append(text)
        return len(text)

    def flush(self) -> None:
        return None


class _Pipe:
    def isatty(self) -> bool:
        return False

    def write(self, text: str) -> int:
        raise AssertionError("progress is quiet when stderr is not a TTY")

    def flush(self) -> None:
        return None


def _record(*, current: int, total: int, kind: str) -> logging.LogRecord:
    record = logging.LogRecord(
        name=LOGGER_NAME,
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="%s/%s %s",
        args=(current, total, kind),
        exc_info=None,
    )
    setattr(record, CURRENT_ATTR, current)
    setattr(record, TOTAL_ATTR, total)
    setattr(record, KIND_ATTR, kind)
    return record


def test_handler_draws_bar_on_tty():
    tty = _TTY()
    ProgressBarHandler(tty).emit(_record(current=4, total=10, kind="cover"))
    assert "".join(tty.chunks) == "\rparch |████░░░░░░| 4/10  cover"


def test_handler_finishes_with_newline():
    tty = _TTY()
    ProgressBarHandler(tty).emit(_record(current=10, total=10, kind="daily"))
    assert "".join(tty.chunks) == "\rparch |██████████| 10/10  daily\n"


def test_handler_quiet_off_tty():
    ProgressBarHandler(_Pipe()).emit(_record(current=4, total=10, kind="cover"))


def test_filter_keeps_only_structured_progress():
    filt = ProgressRecordFilter()
    assert filt.filter(_record(current=1, total=2, kind="cover"))
    plain = logging.LogRecord(
        name=LOGGER_NAME,
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="plain",
        args=(),
        exc_info=None,
    )
    assert not filt.filter(plain)


def test_install_draws_from_logger_info():
    tty = _TTY()
    handler = install_progress_bar(tty)
    try:
        logging.getLogger(LOGGER_NAME).info(
            "%s/%s %s",
            4,
            10,
            "cover",
            extra={
                CURRENT_ATTR: 4,
                TOTAL_ATTR: 10,
                KIND_ATTR: "cover",
            },
        )
        assert "".join(tty.chunks) == "\rparch |████░░░░░░| 4/10  cover"
    finally:
        remove_progress_bar(handler)


def test_press_signature_has_no_progress_hook():
    assert list(inspect.signature(press).parameters) == [
        "spec",
        "output",
        "plotter",
        "overlay",
        "proof",
    ]


def test_year_planner_plot_logs_each_page(caplog):
    caplog.set_level(logging.INFO, logger=LOGGER_NAME)
    spec = Spec(months=(1,), notes_pages=0)
    book = YearPlanner()
    pages = book.pages(spec)
    book.plot(spec, RecordingPlotter())
    records = [r for r in caplog.records if hasattr(r, CURRENT_ATTR)]
    assert [getattr(r, CURRENT_ATTR) for r in records] == list(range(1, len(pages) + 1))
    assert all(getattr(r, TOTAL_ATTR) == len(pages) for r in records)
    assert [getattr(r, KIND_ATTR) for r in records] == [page.kind for page in pages]


def test_projects_notebook_plot_logs_each_page(caplog):
    caplog.set_level(logging.INFO, logger=LOGGER_NAME)
    spec = Spec(notes_pages=1, book="projects-notebook")
    book = ProjectsNotebook()
    pages = book.pages(spec)
    book.plot(spec, RecordingPlotter())
    records = [r for r in caplog.records if hasattr(r, CURRENT_ATTR)]
    assert [getattr(r, CURRENT_ATTR) for r in records] == list(range(1, len(pages) + 1))
    assert all(getattr(r, TOTAL_ATTR) == len(pages) for r in records)
    assert [getattr(r, KIND_ATTR) for r in records] == [page.kind for page in pages]


def test_press_does_not_draw_without_handler(monkeypatch):
    monkeypatch.setattr(sys, "stderr", _Pipe())
    YearPlanner().plot(Spec(months=(1,), notes_pages=0), RecordingPlotter())


def test_plot_plus_handler_draws_projects_notebook():
    tty = _TTY()
    handler = install_progress_bar(tty)
    try:
        spec = Spec(notes_pages=1, book="projects-notebook")
        book = ProjectsNotebook()
        pages = book.pages(spec)
        book.plot(spec, RecordingPlotter())
        text = "".join(tty.chunks)
        assert f"1/{len(pages)}  {pages[0].kind}" in text
        assert text.endswith(f" {len(pages)}/{len(pages)}  {pages[-1].kind}\n")
    finally:
        remove_progress_bar(handler)


def test_cli_installs_handler_only_during_press(monkeypatch, tmp_path):
    seen: list[bool] = []

    def fake_press(spec, output, **kwargs):
        seen.append(
            any(
                isinstance(item, ProgressBarHandler)
                for item in logging.getLogger(LOGGER_NAME).handlers
            )
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"%PDF-1.4\n")
        return output

    monkeypatch.setattr("parch.press.press", fake_press)
    out = tmp_path / "job.pdf"
    assert main(["press", "supernote-nomad", "-o", str(out)]) == 0
    assert seen == [True]
    assert not any(
        isinstance(item, ProgressBarHandler)
        for item in logging.getLogger(LOGGER_NAME).handlers
    )
