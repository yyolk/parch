import inspect
import sys
from typing import Protocol

import pytest

from parch.books import ProjectsNotebook, YearPlanner
from parch.plotter import RecordingPlotter
from parch.press import main, press
from parch.progress import (
    PressSession,
    listeners,
    notify,
    render_progress,
    session,
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


@pytest.fixture(autouse=True)
def _isolate_listeners():
    listeners.clear()
    yield
    listeners.clear()


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


def test_press_signature_has_no_progress_hook():
    assert list(inspect.signature(press).parameters) == [
        "spec",
        "output",
        "plotter",
        "overlay",
        "proof",
    ]


def test_observers_are_a_list_not_a_protocol():
    assert type(listeners) is list
    assert listeners is session.listeners
    assert not issubclass(PressSession, Protocol)
    recorded: list[tuple[int, int, str]] = []
    listeners.append(lambda i, n, label: recorded.append((i, n, label)))
    notify(4, 10, "cover")
    assert recorded == [(4, 10, "cover")]


def test_notify_fans_out_to_every_listener():
    first: list[tuple[int, int, str]] = []
    second: list[tuple[int, int, str]] = []
    listeners.append(lambda i, n, label: first.append((i, n, label)))
    listeners.append(lambda i, n, label: second.append((i, n, label)))
    notify(1, 2, "cover")
    notify(2, 2, "project")
    assert first == [(1, 2, "cover"), (2, 2, "project")]
    assert second == first


def test_notify_is_quiet_with_empty_list(monkeypatch):
    monkeypatch.setattr(sys, "stderr", _Pipe())
    notify(4, 10, "cover")


def test_year_planner_plot_notifies_observers():
    ticks: list[tuple[int, int, str]] = []
    listeners.append(lambda i, n, label: ticks.append((i, n, label)))
    spec = Spec(months=(1,), notes_pages=0)
    book = YearPlanner()
    pages = book.pages(spec)
    book.plot(spec, RecordingPlotter())
    assert [tick[0] for tick in ticks] == list(range(1, len(pages) + 1))
    assert all(tick[1] == len(pages) for tick in ticks)
    assert [tick[2] for tick in ticks] == [page.kind for page in pages]


def test_projects_notebook_plot_notifies_observers():
    ticks: list[tuple[int, int, str]] = []
    listeners.append(lambda i, n, label: ticks.append((i, n, label)))
    spec = Spec(notes_pages=1, book="projects-notebook")
    book = ProjectsNotebook()
    pages = book.pages(spec)
    book.plot(spec, RecordingPlotter())
    assert [tick[0] for tick in ticks] == list(range(1, len(pages) + 1))
    assert all(tick[1] == len(pages) for tick in ticks)
    assert [tick[2] for tick in ticks] == [page.kind for page in pages]


def test_press_does_not_register_the_bar(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "stderr", _Pipe())
    assert listeners == []
    press(
        Spec(book="projects-notebook"),
        tmp_path / "lib.pdf",
        plotter=RecordingPlotter(),
    )
    assert listeners == []


def test_cli_registers_stderr_bar_before_press(monkeypatch, tmp_path):
    seen: list[list] = []

    def fake_press(spec, output, **kwargs):
        seen.append(list(listeners))
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"%PDF-1.4\n")
        return output

    monkeypatch.setattr("parch.press.press", fake_press)
    out = tmp_path / "job.pdf"
    assert main(["press", "supernote-nomad", "-o", str(out)]) == 0
    assert seen == [[render_progress]]
    assert listeners == []


def test_cli_unregisters_bar_after_config_error(monkeypatch, tmp_path, capsys):
    spec = tmp_path / "bad.toml"
    spec.write_text(
        "year = 2026\nmonth = 1\n[typography.overlay]\nschema_version = 99\n"
        "[typography.overlay.chrome]\nsize = 8.6\n",
        encoding="utf-8",
    )
    assert main(["press", str(spec), "-o", str(tmp_path / "ver.pdf")]) == 2
    assert "schema_version" in capsys.readouterr().err
    assert listeners == []
