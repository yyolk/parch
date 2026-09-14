import io

from parch.books import ProjectsNotebook, YearPlanner
from parch.plotter import RecordingPlotter
from parch.press import _stderr_page_bar, main, press
from parch.sections import Page
from parch.spec import Spec


class _Tty(io.StringIO):
    def isatty(self) -> bool:
        return True


class _Pipe(io.StringIO):
    def isatty(self) -> bool:
        return False


def _cover(kind: str = "cover", dest: str = "cover") -> Page:
    return Page(dest=dest, kind=kind, title="Cover", nav=(), components=())


def test_stderr_bar_rewrites_kind_and_final_newline():
    stream = _Tty()
    on_page = _stderr_page_bar(stream)
    assert on_page is not None
    on_page(4, 10, _cover())
    assert stream.getvalue() == "\rparch |████░░░░░░| 4/10  cover\033[K"
    on_page(10, 10, _cover("project", "projects-2026-01"))
    assert stream.getvalue().endswith("\rparch |██████████| 10/10  project\033[K\n")


def test_stderr_bar_quiet_when_not_tty():
    assert _stderr_page_bar(_Pipe()) is None


def test_projects_notebook_plot_calls_on_page():
    spec = Spec(book="projects-notebook")
    pages = ProjectsNotebook().pages(spec)
    seen: list[tuple[int, int, str]] = []
    ProjectsNotebook().plot(
        spec,
        RecordingPlotter(),
        on_page=lambda i, n, page: seen.append((i, n, page.kind)),
    )
    assert [i for i, _, _ in seen] == list(range(1, len(pages) + 1))
    assert seen[0] == (1, len(pages), "cover")
    assert {n for _, n, _ in seen} == {len(pages)}
    assert len(pages) == 10


def test_year_planner_plot_calls_on_page():
    spec = Spec(months=(1,), notes_pages=0)
    pages = YearPlanner().pages(spec)
    seen: list[tuple[int, int, str]] = []
    YearPlanner().plot(
        spec,
        RecordingPlotter(),
        on_page=lambda i, n, page: seen.append((i, n, page.kind)),
    )
    assert seen[0] == (1, len(pages), "cover")
    assert seen[-1][0] == len(pages)
    assert [i for i, _, _ in seen] == list(range(1, len(pages) + 1))


def test_press_forwards_on_page(tmp_path):
    spec = Spec(book="projects-notebook")
    seen: list[tuple[int, int, str]] = []
    press(
        spec,
        tmp_path / "out.pdf",
        on_page=lambda i, n, page: seen.append((i, n, page.kind)),
    )
    assert seen[0] == (1, 10, "cover")
    assert len(seen) == 10


def test_cli_press_passes_bar_callback_when_tty(monkeypatch, tmp_path):
    seen: dict[str, object] = {}

    def fake_press(spec, output, **kwargs):
        seen["on_page"] = kwargs.get("on_page")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"%PDF-1.4\n")
        return output

    monkeypatch.setattr("parch.press.press", fake_press)
    monkeypatch.setattr("parch.press.sys.stderr", _Tty())
    out = tmp_path / "job.pdf"
    assert main(["press", "supernote-nomad", "-o", str(out)]) == 0
    assert callable(seen["on_page"])


def test_cli_press_omits_bar_when_stderr_not_tty(monkeypatch, tmp_path):
    seen: dict[str, object] = {}

    def fake_press(spec, output, **kwargs):
        seen["on_page"] = kwargs.get("on_page")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"%PDF-1.4\n")
        return output

    monkeypatch.setattr("parch.press.press", fake_press)
    monkeypatch.setattr("parch.press.sys.stderr", _Pipe())
    out = tmp_path / "job.pdf"
    assert main(["press", "supernote-nomad", "-o", str(out)]) == 0
    assert seen["on_page"] is None
