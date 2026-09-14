from pathlib import Path

import pytest
from pypdf import PdfReader

from parch import ConfigError
from parch.books import (
    BOOK_NAMES,
    Book,
    ProjectsNotebook,
    YearPlanner,
    book_for,
)
from parch.calendar import month_touching_weeks
from parch.components import CoverTitle, ProjectsBoard, ProjectsIndex
from parch.plotter import RecordingPlotter
from parch.press import main, press
from parch.sections.nav import planner_nav
from parch.spec import Spec


def _named_dests(reader: PdfReader) -> set[str]:
    raw = reader.named_destinations or {}
    return {str(key).lstrip("/") for key in raw}


def _page_dests(spec: Spec) -> list[str]:
    return [
        spec.cover_dest,
        spec.projects_index_dest,
        *[spec.dest_for_project(slot) for slot in range(1, spec.project_count + 1)],
    ]


def _leftover_dests(spec: Spec) -> list[str]:
    """Nav dests CoverSection + ProjectsSection emit that this book does not press."""
    first = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[0]
    nav = planner_nav(spec, week_dest=spec.dest_for_week(first[0]))
    present = set(_page_dests(spec))
    leftovers: list[str] = []
    seen: set[str] = set()
    for dest in (spec.year_dest, *(item.dest for item in nav)):
        if dest not in present and dest not in seen:
            seen.add(dest)
            leftovers.append(dest)
    return leftovers


def _add_dests(plotter: RecordingPlotter) -> dict[str, int]:
    bound: dict[str, int] = {}
    for op in plotter.ops:
        if op[0] == "add_dest":
            bound[op[1]] = op[2]
    return bound


def test_year_planner_and_projects_notebook_are_books():
    assert isinstance(YearPlanner(), Book)
    assert isinstance(ProjectsNotebook(), Book)
    assert book_for("year").__class__ is YearPlanner
    assert book_for("projects").__class__ is ProjectsNotebook
    assert BOOK_NAMES == ("year", "projects")
    with pytest.raises(ConfigError, match="unknown book"):
        book_for("meetings")


def test_projects_notebook_reuses_cover_and_projects_sections():
    spec = Spec(notes_pages=1, months=(1,))
    pages = ProjectsNotebook().pages(spec)
    assert [page.kind for page in pages] == [
        "cover",
        "projects_index",
        *("project",) * spec.project_count,
    ]
    assert [page.dest for page in pages] == _page_dests(spec)
    cover = next(item for item in pages[0].components if isinstance(item, CoverTitle))
    assert cover.subtitle == spec.title
    assert cover.cta_dest == spec.year_dest
    roster = next(
        item for item in pages[1].components if isinstance(item, ProjectsIndex)
    )
    assert len(roster.tickets) == spec.project_tickets
    leaf = next(item for item in pages[2].components if isinstance(item, ProjectsBoard))
    assert leaf.number == 1
    assert leaf.index_dest == spec.projects_index_dest
    kinds = {page.kind for page in pages}
    assert kinds == {"cover", "projects_index", "project"}
    year_pages = YearPlanner().pages(spec)
    assert [p.dest for p in pages] == [
        p.dest for p in year_pages if p.kind in {"cover", "projects_index", "project"}
    ]


def test_projects_notebook_plot_binds_leftover_nav_dests_to_cover():
    spec = Spec(notes_pages=1, months=(1,))
    leftovers = _leftover_dests(spec)
    assert "year-2026" in leftovers
    assert "meetings-index-2026" in leftovers
    assert "2026-01-01" in leftovers
    plotter = RecordingPlotter()
    ProjectsNotebook().plot(spec, plotter)
    dests = plotter.dests()
    assert dests[: 1 + len(leftovers)] == ["cover", *leftovers]
    assert dests[1 + len(leftovers) :] == _page_dests(spec)[1:]
    bound = _add_dests(plotter)
    assert bound["cover"] == 1
    for dest in leftovers:
        assert bound[dest] == 1
    assert bound["projects-index-2026-01"] == 2
    assert bound["projects-2026-01"] == 3
    assert plotter.page == 10


def test_press_projects_book_pdf(tmp_path: Path):
    out = tmp_path / "projects.pdf"
    spec = Spec(notes_pages=1, months=(1,), title="Projects notebook")
    press(spec, out, book=ProjectsNotebook())
    assert out.is_file() and out.stat().st_size > 0
    reader = PdfReader(out)
    assert len(reader.pages) == 10
    dests = _named_dests(reader)
    for dest in _page_dests(spec):
        assert dest in dests
    for dest in _leftover_dests(spec):
        assert dest in dests


def test_cli_press_projects_book(tmp_path: Path):
    spec = tmp_path / "job.toml"
    spec.write_text(
        'year = 2026\ndevice = "supernote-nomad"\nmonth = 1\n'
        'title = "Projects notebook"\n',
        encoding="utf-8",
    )
    out = tmp_path / "job.pdf"
    assert main(["press", str(spec), "--book", "projects", "-o", str(out)]) == 0
    dests = _named_dests(PdfReader(out))
    assert "cover" in dests
    assert "projects-index-2026-01" in dests
    assert "projects-2026-08" in dests
    assert "year-2026" in dests


def test_cli_book_default_stays_year(monkeypatch, tmp_path: Path):
    seen: dict[str, object] = {}

    def fake_press(spec, output, **kwargs):
        seen["book"] = kwargs.get("book")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"%PDF-1.4\n")
        return output

    monkeypatch.setattr("parch.press.press", fake_press)
    out = tmp_path / "year.pdf"
    assert main(["press", "supernote-nomad", "-o", str(out)]) == 0
    assert seen["book"].__class__ is YearPlanner


def test_cli_press_projects_example(tmp_path: Path):
    out = tmp_path / "projects.pdf"
    assert (
        main(["press", "examples/projects.toml", "--book", "projects", "-o", str(out)])
        == 0
    )
    reader = PdfReader(out)
    assert len(reader.pages) == 10
    dests = _named_dests(reader)
    assert "cover" in dests
    assert "projects-index-2026-01" in dests
    assert "projects-2026-08" in dests
