import inspect
import sys

import pytest

from parch import progress
from parch.books import EngineeringPad, ProjectsNotebook, YearPlanner
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.progress import render_progress
from parch.spec import Spec


@pytest.fixture(autouse=True)
def _reset_progress_width():
    progress._last_width = 0
    yield
    progress._last_width = 0


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


def test_render_progress_bar_on_tty(monkeypatch):
    tty = _TTY()
    monkeypatch.setattr(sys, "stderr", tty)
    render_progress(4, 10, "cover")
    assert "".join(tty.chunks) == "\rparch |████░░░░░░| 4/10  cover"


def test_render_progress_finishes_with_newline(monkeypatch):
    tty = _TTY()
    monkeypatch.setattr(sys, "stderr", tty)
    render_progress(10, 10, "daily")
    assert "".join(tty.chunks) == "\rparch |██████████| 10/10  daily\n"


def test_render_progress_quiet_off_tty(monkeypatch):
    monkeypatch.setattr(sys, "stderr", _Pipe())
    render_progress(4, 10, "cover")


def test_render_progress_space_pads_shorter_label(monkeypatch):
    tty = _TTY()
    monkeypatch.setattr(sys, "stderr", tty)
    render_progress(2, 10, "projects_index")
    render_progress(3, 10, "cover")
    long = "parch |██░░░░░░░░| 2/10  projects_index"
    short = "parch |███░░░░░░░| 3/10  cover"
    assert tty.chunks == [f"\r{long}", f"\r{short.ljust(len(long))}"]


def test_press_signature_has_no_progress_hook():
    assert list(inspect.signature(press).parameters) == [
        "spec",
        "output",
        "plotter",
        "overlay",
        "proof",
    ]


def test_year_planner_plot_ticks_each_page(monkeypatch):
    ticks: list[tuple[int, int, str]] = []
    monkeypatch.setattr(
        "parch.books.year_planner.render_progress",
        lambda i, n, label: ticks.append((i, n, label)),
    )
    spec = Spec(months=(1,), notes_pages=0)
    book = YearPlanner()
    pages = book.pages(spec)
    book.plot(spec, RecordingPlotter())
    assert [tick[0] for tick in ticks] == list(range(1, len(pages) + 1))
    assert all(tick[1] == len(pages) for tick in ticks)
    assert [tick[2] for tick in ticks] == [page.kind for page in pages]


def test_projects_notebook_plot_ticks_each_page(monkeypatch):
    ticks: list[tuple[int, int, str]] = []
    monkeypatch.setattr(
        "parch.books.projects_notebook.render_progress",
        lambda i, n, label: ticks.append((i, n, label)),
    )
    spec = Spec(notes_pages=1, book="projects-notebook")
    book = ProjectsNotebook()
    pages = book.pages(spec)
    book.plot(spec, RecordingPlotter())
    assert [tick[0] for tick in ticks] == list(range(1, len(pages) + 1))
    assert all(tick[1] == len(pages) for tick in ticks)
    assert [tick[2] for tick in ticks] == [page.kind for page in pages]


def test_engineering_pad_plot_ticks_each_page(monkeypatch):
    ticks: list[tuple[int, int, str]] = []
    monkeypatch.setattr(
        "parch.books.engineering_pad.render_progress",
        lambda i, n, label: ticks.append((i, n, label)),
    )
    spec = Spec(book="engineering-pad", engineering_pad_sheets=2)
    book = EngineeringPad()
    pages = book.pages(spec)
    book.plot(spec, RecordingPlotter())
    assert [tick[0] for tick in ticks] == list(range(1, len(pages) + 1))
    assert all(tick[1] == len(pages) for tick in ticks)
    assert [tick[2] for tick in ticks] == [page.kind for page in pages]
