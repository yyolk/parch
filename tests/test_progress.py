import inspect
import json
import sys
from pathlib import Path

from parch.books import ProjectsNotebook, YearPlanner
from parch.plotter import RecordingPlotter
from parch.press import main, press
from parch.progress import (
    PROGRESS_FILE_ENV,
    ProgressReport,
    format_bar,
    report_progress,
    resolve_progress_file,
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
    def __init__(self) -> None:
        self.chunks: list[str] = []

    def isatty(self) -> bool:
        return False

    def write(self, text: str) -> int:
        self.chunks.append(text)
        return len(text)

    def flush(self) -> None:
        return None


def test_format_bar_matches_shared_ui():
    assert format_bar(4, 10, "cover") == "parch |████░░░░░░| 4/10  cover"


def test_report_progress_bar_on_tty(monkeypatch):
    tty = _TTY()
    monkeypatch.setattr(sys, "stderr", tty)
    report_progress(4, 10, "cover")
    assert "".join(tty.chunks) == "\rparch |████░░░░░░| 4/10  cover"


def test_report_progress_finishes_with_newline(monkeypatch):
    tty = _TTY()
    monkeypatch.setattr(sys, "stderr", tty)
    report_progress(10, 10, "daily")
    assert "".join(tty.chunks) == "\rparch |██████████| 10/10  daily\n"


def test_report_progress_quiet_off_tty(monkeypatch):
    pipe = _Pipe()
    monkeypatch.setattr(sys, "stderr", pipe)
    report_progress(4, 10, "cover")
    assert pipe.chunks == []


def test_same_tick_writes_tty_and_progress_file(monkeypatch, tmp_path: Path):
    tty = _TTY()
    monkeypatch.setattr(sys, "stderr", tty)
    log = tmp_path / "progress.jsonl"
    report_progress(4, 10, "cover", progress_file=log)
    assert "".join(tty.chunks) == "\rparch |████░░░░░░| 4/10  cover"
    assert log.read_text(encoding="utf-8") == '{"i":4,"n":10,"kind":"cover"}\n'


def test_progress_file_appends_when_stderr_is_not_a_tty(monkeypatch, tmp_path: Path):
    pipe = _Pipe()
    monkeypatch.setattr(sys, "stderr", pipe)
    log = tmp_path / "ci.jsonl"
    report_progress(1, 2, "cover", progress_file=log)
    report_progress(2, 2, "project", progress_file=log)
    assert pipe.chunks == []
    lines = log.read_text(encoding="utf-8").splitlines()
    assert [json.loads(line) for line in lines] == [
        {"i": 1, "n": 2, "kind": "cover"},
        {"i": 2, "n": 2, "kind": "project"},
    ]


def test_resolve_progress_file_flag_wins_over_env(monkeypatch, tmp_path: Path):
    env = tmp_path / "from-env.jsonl"
    flag = tmp_path / "from-flag.jsonl"
    monkeypatch.setenv(PROGRESS_FILE_ENV, str(env))
    assert resolve_progress_file(flag) == flag
    assert resolve_progress_file(None) == env
    monkeypatch.delenv(PROGRESS_FILE_ENV)
    assert resolve_progress_file(None) is None
    assert resolve_progress_file("") is None


def test_progress_report_truncates_then_appends(tmp_path: Path):
    log = tmp_path / "nested" / "run.jsonl"
    log.parent.mkdir()
    log.write_text("stale\n", encoding="utf-8")
    report = ProgressReport(log)
    report(1, 2, "cover")
    report(2, 2, "annual")
    assert [
        json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()
    ] == [
        {"i": 1, "n": 2, "kind": "cover"},
        {"i": 2, "n": 2, "kind": "annual"},
    ]


def test_press_signature_has_progress_file():
    assert list(inspect.signature(press).parameters) == [
        "spec",
        "output",
        "plotter",
        "overlay",
        "proof",
        "progress_file",
    ]


def test_press_writes_progress_file_for_projects_notebook(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(sys, "stderr", _Pipe())
    spec = Spec(notes_pages=1, book="projects-notebook")
    pages = ProjectsNotebook().pages(spec)
    log = tmp_path / "press.jsonl"
    press(spec, tmp_path / "out.pdf", plotter=RecordingPlotter(), progress_file=log)
    records = [
        json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()
    ]
    assert [row["i"] for row in records] == list(range(1, len(pages) + 1))
    assert all(row["n"] == len(pages) for row in records)
    assert [row["kind"] for row in records] == [page.kind for page in pages]


def test_press_progress_file_from_env(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(sys, "stderr", _Pipe())
    log = tmp_path / "env.jsonl"
    monkeypatch.setenv(PROGRESS_FILE_ENV, str(log))
    spec = Spec(notes_pages=1, book="projects-notebook")
    press(spec, tmp_path / "out.pdf", plotter=RecordingPlotter())
    assert log.is_file()
    first = json.loads(log.read_text(encoding="utf-8").splitlines()[0])
    assert first["i"] == 1
    assert first["kind"] == "cover"


def test_year_planner_plot_forwards_ticks():
    ticks: list[tuple[int, int, str]] = []
    spec = Spec(months=(1,), notes_pages=0)
    book = YearPlanner()
    pages = book.pages(spec)
    book.plot(
        spec,
        RecordingPlotter(),
        on_progress=lambda i, n, kind: ticks.append((i, n, kind)),
    )
    assert [tick[0] for tick in ticks] == list(range(1, len(pages) + 1))
    assert all(tick[1] == len(pages) for tick in ticks)
    assert [tick[2] for tick in ticks] == [page.kind for page in pages]


def test_projects_notebook_plot_forwards_ticks():
    ticks: list[tuple[int, int, str]] = []
    spec = Spec(notes_pages=1, book="projects-notebook")
    book = ProjectsNotebook()
    pages = book.pages(spec)
    book.plot(
        spec,
        RecordingPlotter(),
        on_progress=lambda i, n, kind: ticks.append((i, n, kind)),
    )
    assert [tick[0] for tick in ticks] == list(range(1, len(pages) + 1))
    assert all(tick[1] == len(pages) for tick in ticks)
    assert [tick[2] for tick in ticks] == [page.kind for page in pages]


def test_cli_progress_file_flag(monkeypatch, tmp_path: Path):
    seen: dict[str, object] = {}

    def fake_press(spec, output, **kwargs):
        seen["progress_file"] = kwargs.get("progress_file")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"%PDF-1.4\n")
        return output

    monkeypatch.setattr("parch.press.press", fake_press)
    log = tmp_path / "cli.jsonl"
    out = tmp_path / "out.pdf"
    assert (
        main(["press", "supernote-nomad", "-o", str(out), "--progress-file", str(log)])
        == 0
    )
    assert seen["progress_file"] == str(log)


def test_cli_omits_progress_file_when_unset(monkeypatch, tmp_path: Path):
    seen: dict[str, object] = {}

    def fake_press(spec, output, **kwargs):
        seen["progress_file"] = kwargs.get("progress_file")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"%PDF-1.4\n")
        return output

    monkeypatch.setattr("parch.press.press", fake_press)
    out = tmp_path / "out.pdf"
    assert main(["press", "supernote-nomad", "-o", str(out)]) == 0
    assert seen["progress_file"] is None
