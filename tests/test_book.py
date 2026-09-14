from pathlib import Path

import pytest
from fpdf.errors import FPDFException

from parch.books import Book, ProjectsNotebook, YearPlanner, plot_pages
from parch.components import CoverTitle, ProjectsBoard, ProjectsIndex
from parch.devices import get_device
from parch.fonts.ramp import EffectiveRamp
from parch.plotter import RecordingPlotter
from parch.plotter.fpdf2 import Fpdf2Plotter
from parch.spec import Spec

_YEAR_BOOK_KINDS = frozenset(
    {
        "annual",
        "meetings_index",
        "meeting",
        "tasks_index",
        "task",
        "review_index",
        "review",
        "quarter",
        "month",
        "habits",
        "weekly",
        "daily",
        "daily_notes",
    }
)


def test_year_planner_and_projects_notebook_are_books():
    assert isinstance(YearPlanner(), Book)
    assert isinstance(ProjectsNotebook(), Book)


def test_projects_notebook_is_cover_plus_projects():
    spec = Spec(notes_pages=1)
    pages = ProjectsNotebook().pages(spec)
    kinds = [page.kind for page in pages]
    assert kinds == ["cover", "projects_index", *["project"] * spec.project_count]
    assert [page.dest for page in pages] == [
        "cover",
        "projects-index-2026-01",
        *[f"projects-2026-{slot:02d}" for slot in range(1, spec.project_count + 1)],
    ]
    assert not any(page.kind in _YEAR_BOOK_KINDS for page in pages)

    cover = pages[0]
    title = next(item for item in cover.components if isinstance(item, CoverTitle))
    assert title.cta_dest == spec.year_dest

    roster = next(
        item for item in pages[1].components if isinstance(item, ProjectsIndex)
    )
    assert len(roster.tickets) == spec.project_tickets
    board = next(
        item for item in pages[2].components if isinstance(item, ProjectsBoard)
    )
    assert board.number == 1
    assert board.index_dest == "projects-index-2026-01"


def test_projects_notebook_honors_index_pages_knob():
    spec = Spec(notes_pages=0, project_index_pages=2, project_tickets=6)
    pages = ProjectsNotebook().pages(spec)
    assert [page.kind for page in pages].count("projects_index") == 2
    assert [page.kind for page in pages].count("project") == 12
    assert pages[1].dest == "projects-index-2026-01"
    assert pages[2].dest == "projects-index-2026-02"
    assert pages[-1].dest == "projects-2026-12"


def test_plot_pages_reserves_then_paints():
    spec = Spec(notes_pages=0)
    pages = ProjectsNotebook().pages(spec)
    plotter = RecordingPlotter()
    plot_pages(pages, spec, plotter, ramp=EffectiveRamp())

    reserves = [op[1] for op in plotter.ops if op[0] == "reserve_dest"]
    dests = plotter.dests()
    assert reserves == dests == [page.dest for page in pages]

    first_begin = next(i for i, op in enumerate(plotter.ops) if op[0] == "begin_page")
    assert all(op[0] == "reserve_dest" for op in plotter.ops[:first_begin])
    assert plotter.ops[first_begin] == ("begin_page", 1)
    assert plotter.ops[first_begin + 1] == ("add_dest", "cover", 1)


def test_projects_notebook_plot_matches_pages():
    spec = Spec(notes_pages=1)
    book: Book = ProjectsNotebook()
    plotter = RecordingPlotter()
    book.plot(spec, plotter)
    assert plotter.dests() == [page.dest for page in book.pages(spec)]
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Projects" in texts
    assert "Year Book" in texts
    assert "2026" in texts


def test_year_planner_plot_still_uses_helper():
    spec = Spec(notes_pages=0, months=(1,))
    book: Book = YearPlanner()
    pages = book.pages(spec)
    plotter = RecordingPlotter()
    book.plot(spec, plotter)
    assert plotter.dests() == [page.dest for page in pages]
    assert pages[0].kind == "cover"
    assert pages[1].kind == "annual"
    assert pages[2].kind == "projects_index"


def test_projects_notebook_cannot_finish_year_shaped_links(tmp_path: Path):
    """Cover + planner_nav still name year-book dests this walk never reserves."""
    spec = Spec(notes_pages=0)
    device = get_device(spec.device)
    plotter = Fpdf2Plotter(device)
    ProjectsNotebook().plot(spec, plotter)
    with pytest.raises(FPDFException, match="year-2026"):
        plotter.finish(tmp_path / "projects.pdf")
