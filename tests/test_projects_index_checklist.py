import pytest

from parch.books import YearPlanner
from parch.components import ProjectLeaf, ProjectsBoard, ProjectsIndexChecklist
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    INDEX_CHECKLIST_GAP,
    INDEX_CHECKLIST_NAME_W,
    INDEX_CHECKLIST_PAGE_W,
    PROJECT_P,
    TICK,
    paint_projects,
    paint_projects_index_checklist,
    projects_index_checklist,
    projects_index_checklist_row,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.sections.projects_index_checklist import (
    CHECKLIST_NAMES,
    ProjectsIndexChecklistSection,
    checklist_items,
)
from parch.spec import Spec


NAV8 = (
    ("Year", "year-2026"),
    ("Proj", "projects-index-checklist-2026"),
    ("Quar", "quarter-2026-Q1"),
    ("Mon", "month-2026-01"),
    ("Habit", "month-2026-01-habits"),
    ("Week", "week-2026-W01"),
    ("Day", "2026-01-01"),
    ("Notes", "2026-01-01-notes-1"),
)


def _index_pages(spec: Spec | None = None) -> list:
    return ProjectsIndexChecklistSection(spec or Spec(notes_pages=1)).pages()


def test_checklist_not_in_year_book():
    spec = Spec(notes_pages=1)
    kinds = [page.kind for page in YearPlanner().pages(spec)]
    assert kinds.count("projects") == 1
    assert "projects_index_checklist" not in kinds
    assert "project" not in kinds
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "projects")
    assert any(isinstance(item, ProjectsBoard) for item in page.components)
    assert not any(isinstance(item, ProjectsIndexChecklist) for item in page.components)
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Proj" not in texts
    assert "Atlas" not in texts


def test_checklist_page_and_leaves():
    spec = Spec(notes_pages=1)
    pages = _index_pages(spec)
    index = pages[0]
    assert index.dest == "projects-index-checklist-2026"
    assert index.kind == "projects_index_checklist"
    assert index.title == "Projects"
    board = next(item for item in index.components if isinstance(item, ProjectsIndexChecklist))
    assert board.year == 2026
    assert len(board.items) == 12
    assert board.items[0].name == "Atlas"
    assert board.items[0].dest == "project-2026-01"
    assert board.items[0].page == "01"
    assert board.items[-1].name == "Well"
    assert board.items[-1].dest == "project-2026-12"
    assert board.items[-1].page == "12"
    assert [item.name for item in board.items] == list(CHECKLIST_NAMES)

    leaves = [p for p in pages if p.kind == "project"]
    assert len(leaves) == 12
    assert leaves[0].dest == "project-2026-01"
    assert leaves[0].title == "Atlas"
    leaf = next(item for item in leaves[0].components if isinstance(item, ProjectLeaf))
    assert leaf.name == "Atlas"
    assert leaf.page == "01"
    assert leaf.index_dest == "projects-index-checklist-2026"
    assert leaf.tasks == 4
    board = next(item for item in leaves[0].components if isinstance(item, ProjectsBoard))
    assert board.cards == 1


def test_checklist_index_rows_knob():
    spec = Spec(notes_pages=1, project_index_rows=10)
    items = checklist_items(spec)
    assert len(items) == 10
    assert items[-1].name == "Parch"
    assert items[-1].page == "10"
    pages = _index_pages(spec)
    assert len([p for p in pages if p.kind == "project"]) == 10


def test_checklist_tracks():
    well = Rect(4, 20, 110, 90)
    seats = projects_index_checklist(well, 12)
    assert len(seats) == 12
    assert seats[0].y == pytest.approx(well.y)
    assert seats[0].x == pytest.approx(well.x)
    assert seats[-1].bottom == pytest.approx(well.bottom)
    assert seats[1].y > seats[0].bottom
    tick, name, leaders, page = projects_index_checklist_row(seats[0])
    assert tick.x == pytest.approx(seats[0].x)
    assert name.x > tick.x
    assert name.w == pytest.approx(INDEX_CHECKLIST_NAME_W)
    assert leaders.x > name.x
    assert page.w == pytest.approx(INDEX_CHECKLIST_PAGE_W)
    assert page.right == pytest.approx(seats[0].right)
    assert seats[1].y - seats[0].bottom == pytest.approx(INDEX_CHECKLIST_GAP)


def test_paint_checklist_prints_names_pages_ticks_and_links():
    spec = Spec(notes_pages=1)
    page = _index_pages(spec)[0]
    board = next(item for item in page.components if isinstance(item, ProjectsIndexChecklist))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_projects_index_checklist(plotter, well, board)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    for name in CHECKLIST_NAMES:
        assert name in texts
    for number in range(1, 13):
        assert f"{number:02d}" in texts
    assert texts.count("P") == 0
    assert "Todo" not in texts
    assert "PROJECT" not in texts

    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 12

    links = plotter.links()
    assert links == [f"project-2026-{n:02d}" for n in range(1, 13)]

    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []


def test_checklist_header_and_proj_tab_active():
    page = _index_pages()[0]
    assert strip_active(page.kind) == "Proj"
    assert strip_items(page) == NAV8
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Projects" in texts
    assert "2026" in texts
    assert "Proj" in texts
    assert "Atlas" in texts
    assert "Well" in texts
    assert "projects-index-checklist-2026" in plotter.links()
    for n in range(1, 13):
        assert f"project-2026-{n:02d}" in plotter.links()


def test_project_leaf_g_craft_and_index_chip():
    pages = _index_pages()
    leaf_page = next(p for p in pages if p.dest == "project-2026-01")
    assert strip_active(leaf_page.kind) == "Proj"
    assert strip_items(leaf_page) == NAV8
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(leaf_page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Atlas" in texts
    assert "Index" in texts
    assert "P" in texts
    assert "Todo" in texts
    assert plotter.links().count("projects-index-checklist-2026") >= 2
    p_boxes = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(PROJECT_P)
    ]
    assert len(p_boxes) == 1


def test_default_board_painter_untouched():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "projects")
    board = next(item for item in page.components if isinstance(item, ProjectsBoard))
    plotter = RecordingPlotter()
    paint_projects(plotter, well_rect(NOMAD), board)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("P") == 3
    assert "Atlas" not in texts
