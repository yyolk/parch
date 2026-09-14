import inspect
import io
from contextlib import contextmanager

import pytest

from parch.books import ProjectsNotebook, YearPlanner
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.progress import page_progress
from parch.sections import Page
from parch.spec import Spec


class _Tty(io.StringIO):
    def isatty(self) -> bool:
        return True


class _Pipe(io.StringIO):
    def isatty(self) -> bool:
        return False

    def write(self, text: str) -> int:
        raise AssertionError("progress is quiet when the stream is not a TTY")


def _cover(kind: str = "cover", dest: str = "cover") -> Page:
    return Page(dest=dest, kind=kind, title="Cover", nav=(), components=())


def test_page_progress_start_tick_and_done():
    stream = _Tty()
    with page_progress(10, stream=stream) as tick:
        assert stream.getvalue() == "\rparch |░░░░░░░░░░| 0/10"
        tick(4, _cover())
        assert stream.getvalue() == (
            "\rparch |░░░░░░░░░░| 0/10\rparch |████░░░░░░| 4/10  cover"
        )
    assert stream.getvalue().endswith("\rparch |████░░░░░░| 4/10  cover\n")


def test_page_progress_tick_page_autoincrements():
    stream = _Tty()
    with page_progress(10, stream=stream) as tick:
        tick(_cover())
        tick(_cover("annual", "year-2026"))
        assert "\rparch |█░░░░░░░░░| 1/10  cover" in stream.getvalue()
        assert stream.getvalue().endswith("\rparch |██░░░░░░░░| 2/10  annual")
    assert stream.getvalue().endswith("\n")


def test_page_progress_full_bar_then_newline_on_exit():
    stream = _Tty()
    with page_progress(10, stream=stream) as tick:
        tick(10, _cover("project", "projects-2026-01"))
    assert stream.getvalue().endswith("\rparch |██████████| 10/10  project\n")


def test_page_progress_quiet_when_not_tty():
    stream = _Pipe()
    with page_progress(10, stream=stream) as tick:
        tick(4, _cover())


def test_page_progress_done_newlines_after_raise():
    stream = _Tty()
    with pytest.raises(RuntimeError, match="paint"):
        with page_progress(10, stream=stream) as tick:
            tick(1, _cover())
            raise RuntimeError("paint")
    assert stream.getvalue().endswith("\n")


def test_tick_rejects_bad_args():
    stream = _Tty()
    with page_progress(2, stream=stream) as tick:
        with pytest.raises(TypeError, match="tick"):
            tick()
        with pytest.raises(TypeError, match="tick"):
            tick(1, 2, 3)


def test_press_signature_has_no_progress_hook():
    assert list(inspect.signature(press).parameters) == [
        "spec",
        "output",
        "plotter",
        "overlay",
        "proof",
    ]


def test_year_planner_plot_ticks_each_page(monkeypatch):
    ticks: list[tuple[int, str]] = []

    @contextmanager
    def fake_progress(total, stream=None):
        def tick(*args):
            match args:
                case (i, page):
                    ticks.append((i, page.kind))
                case (page,):
                    ticks.append((len(ticks) + 1, page.kind))

        yield tick

    monkeypatch.setattr("parch.books.year_planner.page_progress", fake_progress)
    spec = Spec(months=(1,), notes_pages=0)
    book = YearPlanner()
    pages = book.pages(spec)
    book.plot(spec, RecordingPlotter())
    assert [i for i, _ in ticks] == list(range(1, len(pages) + 1))
    assert [kind for _, kind in ticks] == [page.kind for page in pages]


def test_projects_notebook_writes_bar_through_context_manager(monkeypatch):
    stream = _Tty()
    monkeypatch.setattr("parch.progress.sys.stderr", stream)
    spec = Spec(notes_pages=1, book="projects-notebook")
    ProjectsNotebook().plot(spec, RecordingPlotter())
    text = stream.getvalue()
    assert text.startswith("\rparch |░░░░░░░░░░| 0/10")
    assert "\rparch |█░░░░░░░░░| 1/10  cover" in text
    assert "10/10" in text
    assert text.endswith("\n")


def test_projects_notebook_plot_ticks_each_page(monkeypatch):
    ticks: list[tuple[int, str]] = []

    @contextmanager
    def fake_progress(total, stream=None):
        assert total == 10

        def tick(*args):
            match args:
                case (i, page):
                    ticks.append((i, page.kind))
                case (page,):
                    ticks.append((len(ticks) + 1, page.kind))

        yield tick

    monkeypatch.setattr("parch.books.projects_notebook.page_progress", fake_progress)
    spec = Spec(notes_pages=1, book="projects-notebook")
    book = ProjectsNotebook()
    pages = book.pages(spec)
    book.plot(spec, RecordingPlotter())
    assert len(pages) == 10
    assert ticks[0] == (1, "cover")
    assert [i for i, _ in ticks] == list(range(1, 11))
    assert [kind for _, kind in ticks] == [page.kind for page in pages]
