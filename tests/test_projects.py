import pytest

from parch.books import YearPlanner
from parch.components import ProjectLeaf, ProjectsIndex
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    PROJECT_P,
    PROJECT_STATUS_MARK,
    RULE,
    TICK,
    TOC_DOT,
    paint_project_leaf,
    paint_projects,
    project_card_columns,
    project_card_left_seats,
    project_card_seats,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.spec import Spec


def test_projects_index_and_leaves_after_annual():
    spec = Spec(notes_pages=1)
    pages = YearPlanner().pages(spec)
    assert pages[1].dest == "year-2026"
    index = pages[2]
    assert index.dest == "projects-2026"
    assert index.kind == "projects"
    assert index.title == "Projects"

    board = next(item for item in index.components if isinstance(item, ProjectsIndex))
    assert board.year == 2026
    assert len(board.entries) == 12
    assert [entry.dest for entry in board.entries] == [
        f"project-2026-{n:02d}" for n in range(1, 13)
    ]
    assert [entry.number for entry in board.entries] == [f"{n:02d}" for n in range(1, 13)]

    leaves = pages[3:15]
    assert [page.dest for page in leaves] == [f"project-2026-{n:02d}" for n in range(1, 13)]
    assert all(page.kind == "project" for page in leaves)
    assert all(page.title == "Project" for page in leaves)
    first_leaf = next(item for item in leaves[0].components if isinstance(item, ProjectLeaf))
    assert first_leaf.number == "01"
    assert first_leaf.tasks == 4
    assert first_leaf.dest == "project-2026-01"

    assert pages[15].dest == "quarter-2026-Q1"
    assert strip_active(index.kind) == "Proj"
    assert strip_active(leaves[0].kind) == "Proj"
    expected_strip = (
        ("Year", "year-2026"),
        ("Proj", "projects-2026"),
        ("Quar", "quarter-2026-Q1"),
        ("Mon", "month-2026-01"),
        ("Habit", "month-2026-01-habits"),
        ("Week", "week-2026-W01"),
        ("Day", "2026-01-01"),
        ("Notes", "2026-01-01-notes-1"),
    )
    assert strip_items(index) == expected_strip
    assert strip_items(leaves[0]) == expected_strip


def test_projects_index_paints_writeins_leaders_and_links():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "projects")
    board = next(item for item in page.components if isinstance(item, ProjectsIndex))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_projects(plotter, well, board)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    for name in (
        "Home studio",
        "Garden beds",
        "Language year",
        "Family archive",
        "Project 01",
    ):
        assert name not in texts
    bolds = [op for op in plotter.ops if op[0] == "text" and op[5] is True]
    assert bolds == []
    for number in (f"{n:02d}" for n in range(1, 13)):
        assert number in texts
    assert "P" not in texts
    assert "Todo" not in texts

    links = [op[2] for op in plotter.ops if op[0] == "link"]
    assert links == [f"project-2026-{n:02d}" for n in range(1, 13)]

    underlines = [
        op
        for op in plotter.ops
        if op[0] == "line" and op[5] == pytest.approx(RULE)
    ]
    assert len(underlines) == 12

    dots = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[3]
        and not op[2]
        and op[1].w == pytest.approx(TOC_DOT)
    ]
    assert len(dots) > 12 * 8


def test_project_leaf_paints_g_card_with_writein_name():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.dest == "project-2026-01")
    leaf = next(item for item in page.components if isinstance(item, ProjectLeaf))
    plotter = RecordingPlotter()
    paint_project_leaf(plotter, Rect(4, 20, 110, 90), leaf)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Home studio" not in texts
    assert texts.count("P") == 1
    assert texts.count("Todo") == 1
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 4
    marks = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[2]
        and not op[3]
        and op[1].w == pytest.approx(PROJECT_STATUS_MARK)
    ]
    assert len(marks) == 3
    p_boxes = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(PROJECT_P)
    ]
    assert len(p_boxes) == 1
    name_rules = [
        op
        for op in plotter.ops
        if op[0] == "line" and op[5] == pytest.approx(RULE)
    ]
    assert name_rules


def test_project_card_tracks():
    well = Rect(4, 20, 110, 90)
    cards = project_card_seats(well, 1)
    assert len(cards) == 1
    left, right = project_card_columns(cards[0])
    header, tasks, status = project_card_left_seats(left)
    assert header.y == pytest.approx(left.y)
    assert status.bottom == pytest.approx(left.bottom)
    assert right.w > left.w


def test_projects_knobs_from_spec():
    spec = Spec(notes_pages=1, project_slots=10, project_tasks=5)
    pages = [p for p in YearPlanner().pages(spec) if p.kind in {"projects", "project"}]
    assert len(pages) == 11
    board = next(item for item in pages[0].components if isinstance(item, ProjectsIndex))
    assert len(board.entries) == 10
    assert board.entries[0].dest == "project-2026-01"
    leaf = next(item for item in pages[1].components if isinstance(item, ProjectLeaf))
    assert leaf.tasks == 5
    plotter = RecordingPlotter()
    paint_project_leaf(plotter, Rect(4, 20, 110, 90), leaf)
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 5


def test_projects_header_year_proj_tab_and_index_chip():
    spec = Spec(notes_pages=1)
    index = next(p for p in YearPlanner().pages(spec) if p.kind == "projects")
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(index, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Projects" in texts
    assert "2026" in texts
    assert "Proj" in texts
    for label in ("Year", "Proj", "Quar", "Mon", "Habit", "Week", "Day", "Notes"):
        assert label in texts
    assert "Home studio" not in texts
    assert plotter.links().count("project-2026-01") >= 1

    leaf = next(p for p in YearPlanner().pages(spec) if p.dest == "project-2026-01")
    ink = RecordingPlotter()
    ink.begin_page()
    PlannerLayout().paint(leaf, ink, NOMAD)
    leaf_texts = [op[2] for op in ink.ops if op[0] == "text"]
    assert "Home studio" not in leaf_texts
    assert "Project" in leaf_texts
    assert "01" in leaf_texts
    assert "Index" in leaf_texts
    assert "projects-2026" in ink.links()
    assert strip_items(leaf)[1] == ("Proj", "projects-2026")
