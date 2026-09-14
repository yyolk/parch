"""Press progress — tiny Progress Protocol (P3), not a callback or plotter hook."""

import io
from pathlib import Path

from parch.books import ProjectsNotebook, YearPlanner
from parch.plotter import RecordingPlotter
from parch.press import main, press
from parch.progress import (
    NullProgress,
    Progress,
    StderrBar,
    bar_line,
    reporter_for,
)
from parch.spec import Spec


class _Tty(io.StringIO):
    def isatty(self) -> bool:
        return True


class _Pipe(io.StringIO):
    def isatty(self) -> bool:
        return False


class _Log:
    """Structural Progress stand-in — records the three Protocol calls."""

    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []

    def start(self, total: int) -> None:
        self.calls.append(("start", total))

    def advance(self, page: str) -> None:
        self.calls.append(("advance", page))

    def done(self) -> None:
        self.calls.append(("done",))


def test_bar_line_is_shared_stderr_format():
    assert bar_line(4, 10, "cover") == "parch |████░░░░░░| 4/10  cover"
    assert bar_line(0, 10, "") == "parch |░░░░░░░░░░| 0/10  "
    assert bar_line(10, 10, "year-2026") == "parch |██████████| 10/10  year-2026"
    assert bar_line(1, 3, "cover") == "parch |███░░░░░░░| 1/3  cover"


def test_null_progress_is_silent(capsys):
    reporter: Progress = NullProgress()
    reporter.start(4)
    reporter.advance("cover")
    reporter.done()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_stderr_bar_writes_cr_on_tty():
    stream = _Tty()
    bar = StderrBar(stream)
    bar.start(10)
    bar.advance("cover")
    bar.advance("year-2026")
    bar.done()
    text = stream.getvalue()
    assert "\r" in text
    assert bar_line(1, 10, "cover") in text
    assert bar_line(4, 10, "cover") not in text
    assert bar_line(2, 10, "year-2026") in text
    assert text.endswith("\n")


def test_stderr_bar_is_quiet_when_not_a_tty():
    stream = _Pipe()
    bar = StderrBar(stream)
    bar.start(10)
    bar.advance("cover")
    bar.done()
    assert stream.getvalue() == ""


def test_stderr_bar_default_stream_without_isatty_is_quiet():
    stream = io.StringIO()
    bar = StderrBar(stream)
    bar.start(2)
    bar.advance("cover")
    bar.done()
    assert stream.getvalue() == ""


def test_reporter_for_tty_is_stderr_bar():
    assert isinstance(reporter_for(_Tty()), StderrBar)


def test_reporter_for_pipe_is_null_progress():
    assert isinstance(reporter_for(_Pipe()), NullProgress)
    assert isinstance(reporter_for(io.StringIO()), NullProgress)


def test_projects_notebook_plot_drives_progress_protocol():
    spec = Spec(book="projects-notebook")
    pages = ProjectsNotebook().pages(spec)
    log = _Log()
    ProjectsNotebook().plot(spec, RecordingPlotter(), progress=log)
    dests = [page.dest for page in pages]
    assert log.calls[0] == ("start", len(pages))
    assert [call[1] for call in log.calls[1:-1]] == dests
    assert log.calls[-1] == ("done",)
    assert dests[0] == "cover"


def test_year_planner_plot_drives_progress_protocol():
    spec = Spec(months=(1,), notes_pages=0)
    pages = YearPlanner().pages(spec)
    log = _Log()
    YearPlanner().plot(spec, RecordingPlotter(), progress=log)
    dests = [page.dest for page in pages]
    assert log.calls[0] == ("start", len(pages))
    assert [call[1] for call in log.calls[1:-1]] == dests
    assert dests[0] == "cover"
    assert log.calls[-1] == ("done",)


def test_press_forwards_progress(tmp_path: Path):
    spec = Spec(book="projects-notebook")
    log = _Log()
    out = tmp_path / "notebook.pdf"
    press(spec, out, progress=log)
    assert out.is_file()
    assert log.calls[0][0] == "start"
    assert log.calls[1] == ("advance", "cover")
    assert log.calls[-1] == ("done",)
    assert log.calls[0][1] == len(log.calls) - 2


def test_press_without_progress_stays_quiet(tmp_path: Path, capsys):
    press(Spec(book="projects-notebook"), tmp_path / "quiet.pdf")
    captured = capsys.readouterr()
    assert "parch |" not in captured.err
    assert captured.err == ""


def test_cli_passes_stderr_bar_when_tty(monkeypatch, tmp_path: Path):
    seen: dict[str, object] = {}

    def fake_press(spec, output, **kwargs):
        seen["progress"] = kwargs.get("progress")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"%PDF-1.4\n")
        return output

    monkeypatch.setattr("parch.press.press", fake_press)
    monkeypatch.setattr("sys.stderr", _Tty())
    out = tmp_path / "tty.pdf"
    assert main(["press", "supernote-nomad", "-o", str(out)]) == 0
    assert isinstance(seen["progress"], StderrBar)


def test_cli_passes_null_progress_when_not_tty(monkeypatch, tmp_path: Path):
    seen: dict[str, object] = {}

    def fake_press(spec, output, **kwargs):
        seen["progress"] = kwargs.get("progress")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"%PDF-1.4\n")
        return output

    monkeypatch.setattr("parch.press.press", fake_press)
    monkeypatch.setattr("sys.stderr", _Pipe())
    out = tmp_path / "pipe.pdf"
    assert main(["press", "supernote-nomad", "-o", str(out)]) == 0
    assert isinstance(seen["progress"], NullProgress)
