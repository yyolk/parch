"""P2 — progress advances on plotter ``begin_page``, not a press callback."""

import io
from pathlib import Path

from parch.books import ProjectsNotebook, YearPlanner
from parch.plotter import ProgressPlotter, RecordingPlotter
from parch.press import main, press
from parch.progress import TtyProgress, format_bar
from parch.spec import Spec


class _TTY(io.StringIO):
    def isatty(self) -> bool:
        return True


class _Pipe(io.StringIO):
    def isatty(self) -> bool:
        return False


def test_format_bar_matches_shared_ui():
    assert format_bar(4, 10, "cover") == "parch |████░░░░░░| 4/10  cover"
    assert format_bar(10, 10, "daily") == "parch |██████████| 10/10  daily"
    assert format_bar(0, 10, "cover") == "parch |░░░░░░░░░░| 0/10  cover"
    assert format_bar(1, 3, "") == "parch |███░░░░░░░| 1/3"


def test_tty_progress_rewrites_line_and_final_newline():
    stream = _TTY()
    bar = TtyProgress(stream)
    assert bar.enabled
    bar(1, 10, "cover")
    bar(4, 10, "annual")
    text = stream.getvalue()
    assert text.startswith("\r")
    assert "parch |█░░░░░░░░░| 1/10  cover" in text
    assert "parch |████░░░░░░| 4/10  annual" in text
    assert not text.endswith("\n")
    bar(10, 10, "daily")
    assert stream.getvalue().endswith("\n")


def test_tty_progress_quiet_when_not_a_tty():
    stream = _Pipe()
    bar = TtyProgress(stream)
    assert not bar.enabled
    bar(1, 2, "cover")
    bar(2, 2, "annual")
    bar.close()
    assert stream.getvalue() == ""


def test_recording_begin_page_fires_attached_sink():
    seen: list[tuple[int, int, str]] = []
    plotter = RecordingPlotter(progress=lambda *step: seen.append(step))
    plotter.expect_pages(("cover", "annual", "month"))
    plotter.begin_page()
    plotter.begin_page()
    plotter.begin_page()
    assert seen == [
        (1, 3, "cover"),
        (2, 3, "annual"),
        (3, 3, "month"),
    ]
    assert [op for op in plotter.ops if op[0] == "begin_page"] == [
        ("begin_page", 1),
        ("begin_page", 2),
        ("begin_page", 3),
    ]


def test_progress_plotter_wrapper_hooks_inner_begin_page():
    inner = RecordingPlotter()
    seen: list[tuple[int, int, str]] = []
    plotter = ProgressPlotter(inner, lambda *step: seen.append(step))
    plotter.expect_pages(("cover", "project"))
    plotter.begin_page()
    plotter.begin_page()
    assert seen == [(1, 2, "cover"), (2, 2, "project")]
    assert inner.page == 2


def test_year_planner_expect_pages_before_begin_page():
    spec = Spec(months=(1,), notes_pages=0)
    pages = YearPlanner().pages(spec)
    seen: list[tuple[int, int, str]] = []
    plotter = RecordingPlotter(progress=lambda *step: seen.append(step))
    YearPlanner().plot(spec, plotter)
    assert len(seen) == len(pages) == plotter.page
    assert seen[0] == (1, len(pages), "cover")
    assert [kind for _, _, kind in seen] == [page.kind for page in pages]
    assert seen[-1][0] == len(pages)


def test_projects_notebook_begin_page_hook_uses_page_kinds():
    spec = Spec(book="projects-notebook")
    pages = ProjectsNotebook().pages(spec)
    seen: list[tuple[int, int, str]] = []
    plotter = RecordingPlotter(progress=lambda *step: seen.append(step))
    ProjectsNotebook().plot(spec, plotter)
    assert seen == [(i, len(pages), page.kind) for i, page in enumerate(pages, start=1)]


def test_press_attaches_sink_when_stderr_is_tty(monkeypatch, tmp_path: Path):
    stream = _TTY()
    monkeypatch.setattr("parch.progress.sys.stderr", stream)
    out = tmp_path / "projects.pdf"
    press(Spec(book="projects-notebook"), out)
    text = stream.getvalue()
    assert "parch |" in text
    assert "cover" in text
    assert text.endswith("\n")
    assert out.is_file()


def test_press_quiet_when_stderr_is_not_a_tty(monkeypatch, tmp_path: Path):
    stream = _Pipe()
    monkeypatch.setattr("parch.progress.sys.stderr", stream)
    out = tmp_path / "projects.pdf"
    press(Spec(book="projects-notebook"), out)
    assert stream.getvalue() == ""
    assert out.is_file()


def test_cli_press_progress_on_tty(monkeypatch, tmp_path: Path):
    stream = _TTY()
    monkeypatch.setattr("parch.progress.sys.stderr", stream)
    spec = tmp_path / "job.toml"
    spec.write_text(
        'year = 2026\ndevice = "supernote-nomad"\nbook = "projects-notebook"\n',
        encoding="utf-8",
    )
    out = tmp_path / "job.pdf"
    assert main(["press", str(spec), "-o", str(out)]) == 0
    text = stream.getvalue()
    assert "\rparch |" in text
    assert "cover" in text
    assert text.endswith("\n")
