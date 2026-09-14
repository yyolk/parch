import inspect
import sys
from types import SimpleNamespace

from parch.books import ProjectsNotebook, YearPlanner
from parch.devices import get_device
from parch.layouts.planner import PlannerLayout
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.progress import plot_pages, render_progress, track
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


def test_track_ticks_after_each_yield():
    pages = [SimpleNamespace(kind="cover"), SimpleNamespace(kind="annual")]
    events: list[tuple[object, ...]] = []

    def bar(i: int, n: int, label: str) -> None:
        events.append(("bar", i, n, label))

    for page in track(pages, bar=bar):
        events.append(("yield", page.kind))

    assert events == [
        ("yield", "cover"),
        ("bar", 1, 2, "cover"),
        ("yield", "annual"),
        ("bar", 2, 2, "annual"),
    ]


def test_track_empty_is_silent():
    ticks: list[int] = []
    assert list(track([], bar=lambda i, n, label: ticks.append(i))) == []
    assert ticks == []


def test_plot_pages_paints_by_consuming_track(monkeypatch):
    consumed: list[str] = []
    real_track = track

    def wrapped(pages, *, bar=None):
        for page in real_track(pages, bar=bar):
            consumed.append(page.kind)
            yield page

    monkeypatch.setattr("parch.progress.track", wrapped)
    spec = Spec(notes_pages=1, book="projects-notebook")
    book = ProjectsNotebook()
    pages = book.pages(spec)
    ticks: list[tuple[int, int, str]] = []
    plot_pages(
        pages,
        RecordingPlotter(),
        PlannerLayout(ramp=book.ramp),
        get_device(spec.device),
        bar=lambda i, n, label: ticks.append((i, n, label)),
    )
    assert consumed == [page.kind for page in pages]
    assert [tick[2] for tick in ticks] == consumed


def test_press_signature_has_no_progress_hook():
    assert list(inspect.signature(press).parameters) == [
        "spec",
        "output",
        "plotter",
        "overlay",
        "proof",
    ]


def test_year_planner_plot_ticks_via_iteration(monkeypatch):
    ticks: list[tuple[int, int, str]] = []
    monkeypatch.setattr(
        "parch.progress.render_progress",
        lambda i, n, label: ticks.append((i, n, label)),
    )
    spec = Spec(months=(1,), notes_pages=0)
    book = YearPlanner()
    pages = book.pages(spec)
    book.plot(spec, RecordingPlotter())
    assert [tick[0] for tick in ticks] == list(range(1, len(pages) + 1))
    assert all(tick[1] == len(pages) for tick in ticks)
    assert [tick[2] for tick in ticks] == [page.kind for page in pages]


def test_projects_notebook_plot_ticks_via_iteration(monkeypatch):
    ticks: list[tuple[int, int, str]] = []
    monkeypatch.setattr(
        "parch.progress.render_progress",
        lambda i, n, label: ticks.append((i, n, label)),
    )
    spec = Spec(notes_pages=1, book="projects-notebook")
    book = ProjectsNotebook()
    pages = book.pages(spec)
    book.plot(spec, RecordingPlotter())
    assert [tick[0] for tick in ticks] == list(range(1, len(pages) + 1))
    assert all(tick[1] == len(pages) for tick in ticks)
    assert [tick[2] for tick in ticks] == [page.kind for page in pages]
