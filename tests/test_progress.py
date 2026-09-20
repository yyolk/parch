import inspect
import sys
from pathlib import Path

from parch.books import (
    BulletJournal,
    EngineeringNotebook,
    ProjectsNotebook,
    YearPlanner,
)
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.progress import render_progress
from parch.spec import Spec

_EL = "\033[K"


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
    assert "".join(tty.chunks) == f"\rparch |████░░░░░░| 4/10  cover{_EL}"


def test_render_progress_finishes_with_newline(monkeypatch):
    tty = _TTY()
    monkeypatch.setattr(sys, "stderr", tty)
    render_progress(10, 10, "daily")
    assert "".join(tty.chunks) == f"\rparch |██████████| 10/10  daily{_EL}\n"


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
    assert tty.chunks == [f"\r{long}{_EL}", f"\r{short}{_EL}"]


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
        "parch.books.protocol.render_progress",
        lambda i, n, label: ticks.append((i, n, label)),
    )
    spec = Spec(months=(1,), notes_pages=0)
    book = YearPlanner()
    pages = book.pages(spec)
    book.plot(spec, RecordingPlotter())
    assert [tick[0] for tick in ticks] == list(range(1, len(pages) + 1))
    assert all(tick[1] == len(pages) for tick in ticks)
    assert [tick[2] for tick in ticks] == [page.kind for page in pages]


def test_engineering_pad_press_ticks_each_face(tmp_path: Path, monkeypatch):
    ticks: list[tuple[int, int, str]] = []
    monkeypatch.setattr(
        "parch.books.protocol.render_progress",
        lambda i, n, label: ticks.append((i, n, label)),
    )
    spec = Spec(engineering_sheets=1)
    press(spec, tmp_path / "pad.pdf", plotter=RecordingPlotter())
    assert ticks == [
        (1, 2, "engineering_front"),
        (2, 2, "engineering_back"),
    ]


def test_steno_pad_press_ticks_each_sheet(tmp_path: Path, monkeypatch):
    ticks: list[tuple[int, int, str]] = []
    monkeypatch.setattr(
        "parch.books.protocol.render_progress",
        lambda i, n, label: ticks.append((i, n, label)),
    )
    spec = Spec(steno_sheets=2)
    press(spec, tmp_path / "steno.pdf", plotter=RecordingPlotter())
    assert ticks == [
        (1, 2, "steno"),
        (2, 2, "steno"),
    ]


def test_stitched_pads_tick_each_exclusive_run(tmp_path: Path, monkeypatch):
    ticks: list[tuple[int, int, str]] = []
    monkeypatch.setattr(
        "parch.books.protocol.render_progress",
        lambda i, n, label: ticks.append((i, n, label)),
    )
    spec = Spec(engineering_sheets=1, steno_sheets=1)
    press(spec, tmp_path / "pads.pdf")
    assert ticks == [
        (1, 2, "engineering_front"),
        (2, 2, "engineering_back"),
        (1, 1, "steno"),
    ]


def test_projects_notebook_plot_ticks_each_page(monkeypatch):
    ticks: list[tuple[int, int, str]] = []
    monkeypatch.setattr(
        "parch.books.protocol.render_progress",
        lambda i, n, label: ticks.append((i, n, label)),
    )
    spec = Spec(notes_pages=1, book="projects-notebook")
    book = ProjectsNotebook()
    pages = book.pages(spec)
    book.plot(spec, RecordingPlotter())
    assert [tick[0] for tick in ticks] == list(range(1, len(pages) + 1))
    assert all(tick[1] == len(pages) for tick in ticks)
    assert [tick[2] for tick in ticks] == [page.kind for page in pages]


def test_bullet_journal_plot_ticks_each_page(monkeypatch):
    ticks: list[tuple[int, int, str]] = []
    monkeypatch.setattr(
        "parch.books.protocol.render_progress",
        lambda i, n, label: ticks.append((i, n, label)),
    )
    spec = Spec(
        book="bullet-journal",
        months=(1,),
        bujo_index_pages=1,
        bujo_collections=1,
    )
    book = BulletJournal()
    pages = book.pages(spec)
    book.plot(spec, RecordingPlotter())
    assert [tick[0] for tick in ticks] == list(range(1, len(pages) + 1))
    assert all(tick[1] == len(pages) for tick in ticks)
    assert [tick[2] for tick in ticks] == [page.kind for page in pages]


def test_engineering_notebook_plot_ticks_each_page(monkeypatch):
    ticks: list[tuple[int, int, str]] = []
    monkeypatch.setattr(
        "parch.books.protocol.render_progress",
        lambda i, n, label: ticks.append((i, n, label)),
    )
    spec = Spec(book="engineering-notebook", engineering_sheets=1)
    book = EngineeringNotebook()
    pages = book.pages(spec)
    book.plot(spec, RecordingPlotter())
    assert [tick[0] for tick in ticks] == list(range(1, len(pages) + 1))
    assert all(tick[1] == len(pages) for tick in ticks)
    assert [tick[2] for tick in ticks] == [page.kind for page in pages]
