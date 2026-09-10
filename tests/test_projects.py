import pytest

from parch.books import YearPlanner
from parch.components import ProjectLeaf, ProjectsBoard, ProjectsIndex
from parch.components.projects import SAMPLE_TITLES, sample_titles
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    DIRECTORY_COL_GAP,
    LEAF_DOT,
    LEAF_SPINE_W,
    PROJECT_COL_WEIGHTS,
    PROJECT_P,
    PROJECT_STATUS_H,
    PROJECT_STATUS_MARK,
    TICK,
    directory_column_counts,
    paint_project,
    paint_projects,
    paint_projects_index_directory,
    project_card_columns,
    project_card_left_seats,
    project_card_seats,
    project_leaf_seats,
    projects_directory_columns,
    projects_directory_rows,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.spec import Spec

NAV8 = (
    ("Year", "year-2026"),
    ("Quar", "quarter-2026-Q1"),
    ("Mon", "month-2026-01"),
    ("Habit", "month-2026-01-habits"),
    ("Week", "week-2026-W01"),
    ("Day", "2026-01-01"),
    ("Notes", "2026-01-01-notes-1"),
    ("Proj", "projects-2026"),
)


def test_projects_directory_after_annual():
    spec = Spec(notes_pages=1)
    pages = YearPlanner().pages(spec)
    assert pages[1].dest == "year-2026"
    page = pages[2]
    assert page.dest == "projects-2026"
    assert page.kind == "projects"
    assert page.title == "Projects"
    assert pages[3].dest == "project-1"
    assert pages[14].dest == "project-12"
    assert pages[15].dest == "quarter-2026-Q1"

    index = next(item for item in page.components if isinstance(item, ProjectsIndex))
    assert index.year == 2026
    assert index.names == SAMPLE_TITLES[:12]
    assert index.dests == tuple(f"project-{n}" for n in range(1, 13))

    assert strip_active(page.kind) == "Proj"
    assert strip_items(page) == NAV8


def test_project_card_tracks():
    well = Rect(4, 20, 110, 90)
    cards = project_card_seats(well, 3)
    assert len(cards) == 3
    assert cards[0].y == pytest.approx(well.y)
    assert cards[0].x == pytest.approx(well.x)
    assert cards[0].w == pytest.approx(well.w)
    assert cards[-1].bottom == pytest.approx(well.bottom)
    assert cards[1].y > cards[0].bottom
    assert cards[2].y > cards[1].bottom

    left, right = project_card_columns(cards[0])
    assert left.x > cards[0].x
    assert right.right < cards[0].right
    assert left.right < right.x
    assert right.w > left.w
    share = left.w + right.w
    assert left.w / share == pytest.approx(PROJECT_COL_WEIGHTS[0] / sum(PROJECT_COL_WEIGHTS))

    header, tasks, status = project_card_left_seats(left)
    assert header.y == pytest.approx(left.y)
    assert header.x == pytest.approx(left.x)
    assert tasks.y > header.bottom
    assert status.y > tasks.bottom
    assert status.bottom == pytest.approx(left.bottom)
    assert status.h == pytest.approx(PROJECT_STATUS_H)


def test_projects_paint_cards_ticks_and_status():
    board = ProjectsBoard(year=2026, cards=3, tasks=4)
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_projects(plotter, well, board)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("P") == 3
    assert texts.count("Todo") == 3
    assert texts.count("Doing") == 3
    assert texts.count("Done") == 3
    assert "PROJECT" not in texts
    assert "Focus" not in texts
    assert "Notes" not in texts

    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 3 * 4

    marks = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[2]
        and not op[3]
        and op[1].w == pytest.approx(PROJECT_STATUS_MARK)
    ]
    assert len(marks) == 9

    p_boxes = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(PROJECT_P)
    ]
    assert len(p_boxes) == 3

    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []


def test_projects_knobs_from_spec():
    spec = Spec(notes_pages=1, project_cards=2, project_tasks=5)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "project")
    leaf = next(item for item in page.components if isinstance(item, ProjectLeaf))
    assert leaf.tasks == 5
    plotter = RecordingPlotter()
    paint_projects(plotter, Rect(4, 20, 110, 90), ProjectsBoard(2026, spec.project_cards, 5))
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 2 * 5
    assert [op[2] for op in plotter.ops if op[0] == "text"].count("P") == 2


def test_projects_header_year_and_eight_tabs():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "projects")
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Projects" in texts
    assert "2026" in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Week", "Day", "Notes", "Proj"):
        assert label in texts
    for name in SAMPLE_TITLES[:12]:
        assert name in texts


def test_directory_column_tracks():
    well = well_rect(NOMAD)
    left, right = projects_directory_columns(well)
    assert left.x == pytest.approx(well.x)
    assert right.right == pytest.approx(well.right)
    assert right.x == pytest.approx(left.right + DIRECTORY_COL_GAP)
    assert left.w == pytest.approx(right.w)

    left_n, right_n = directory_column_counts(12)
    assert (left_n, right_n) == (6, 6)
    seats = projects_directory_rows(left, left_n)
    assert len(seats) == 6
    assert seats[0].y == pytest.approx(left.y)
    assert seats[-1].bottom == pytest.approx(left.bottom)
    for earlier, later in zip(seats, seats[1:]):
        assert later.y == pytest.approx(earlier.bottom)

    assert directory_column_counts(11) == (6, 5)


def test_paint_directory_prints_names_and_links_leaves():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "projects")
    index = next(item for item in page.components if isinstance(item, ProjectsIndex))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_projects_index_directory(plotter, well, index)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    for name in SAMPLE_TITLES[:12]:
        assert name in texts
    assert "P" not in texts
    assert "Todo" not in texts
    assert "Focus" not in texts
    assert texts.count("______") == 0

    links = plotter.links()
    assert links == [f"project-{n}" for n in range(1, 13)]
    left, right = projects_directory_columns(well)
    for op in plotter.ops:
        if op[0] == "link":
            assert op[1].w == pytest.approx(left.w) or op[1].w == pytest.approx(right.w)


def test_directory_proj_tab_active_and_annual_lands_there():
    spec = Spec(notes_pages=1)
    pages = YearPlanner().pages(spec)
    index = next(p for p in pages if p.kind == "projects")
    assert strip_active(index.kind) == "Proj"
    assert strip_items(index) == NAV8

    annual = next(p for p in pages if p.kind == "annual")
    assert ("Proj", "projects-2026") in strip_items(annual)

    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(index, plotter, NOMAD)
    assert plotter.links().count("project-1") == 1
    assert "projects-2026" in plotter.links()
    assert "North Cabin" in [op[2] for op in plotter.ops if op[0] == "text"]


def test_project_leaf_prints_name_and_links_back():
    spec = Spec(notes_pages=1)
    pages = YearPlanner().pages(spec)
    leaf_page = next(p for p in pages if p.dest == "project-1")
    assert leaf_page.kind == "project"
    assert leaf_page.title == "North Cabin"
    assert strip_active(leaf_page.kind) == "Proj"
    assert strip_items(leaf_page) == NAV8

    leaf = next(item for item in leaf_page.components if isinstance(item, ProjectLeaf))
    assert leaf.year == 2026
    assert leaf.number == 1
    assert leaf.name == "North Cabin"
    assert leaf.tasks == 4
    assert leaf.index_dest == "projects-2026"

    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(leaf_page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "North Cabin" in texts
    assert "Index" in texts
    assert "2026" in texts
    assert "P" in texts
    assert "In Progress" in texts
    assert plotter.links().count("projects-2026") >= 2

    well = well_rect(NOMAD)
    ink = RecordingPlotter()
    paint_project(ink, well, leaf)
    ink_texts = [op[2] for op in ink.ops if op[0] == "text"]
    assert ink_texts.count("North Cabin") == 1
    assert ink_texts.count("P") == 1
    assert "Todo" in ink_texts
    assert "In Progress" in ink_texts
    assert "Done" in ink_texts
    spines = [
        op
        for op in ink.ops
        if op[0] == "rect" and op[3] and op[1].w == pytest.approx(LEAF_SPINE_W)
    ]
    assert len(spines) == 1
    dots = [
        op
        for op in ink.ops
        if op[0] == "rect" and op[3] and op[1].w == pytest.approx(LEAF_DOT)
    ]
    assert len(dots) > 20
    board, rail = project_leaf_seats(well)
    assert board.right < rail.x
    assert rail.right == pytest.approx(well.right)


def test_project_index_rows_knob():
    spec = Spec(notes_pages=1, project_index_rows=10)
    pages = YearPlanner().pages(spec)
    index = next(p for p in pages if p.kind == "projects")
    roster = next(item for item in index.components if isinstance(item, ProjectsIndex))
    assert roster.names == sample_titles(10)
    assert len(roster.dests) == 10
    dests = [p.dest for p in pages]
    assert dests.count("project-10") == 1
    assert "project-11" not in dests
