import pytest

from parch.books import YearPlanner
from parch.components import ProjectLeaf, ProjectsBoard, ProjectsIndexSpines
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    INDEX_SPINE_AIR,
    INDEX_SPINE_FOOT_H,
    INDEX_SPINE_GAP,
    INDEX_SPINE_HEAD,
    INDEX_SPINE_PLANK,
    INDEX_SPINE_ROW_GAP,
    INDEX_SPINE_W,
    PROJECT_P,
    RULE_C,
    PROJECT_STATUS_MARK,
    TICK,
    paint_project,
    paint_projects_index_spines,
    project_card_seats,
    projects_index_spine_planks,
    projects_index_spine_row_count,
    projects_index_spine_row_counts,
    projects_index_spine_seats,
    projects_index_spine_shelves,
    projects_index_spine_writeins,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.sections.projects_index_spines import ProjectsIndexSpinesSection, spine_catalog
from parch.spec import Spec


def _index_pages(spec: Spec | None = None) -> list:
    return ProjectsIndexSpinesSection(spec or Spec(notes_pages=1)).pages()


def test_index_spines_not_in_year_book():
    kinds = [page.kind for page in YearPlanner().pages(Spec(notes_pages=1))]
    assert kinds.count("projects") == 1
    assert "projects_index_spines" not in kinds
    assert "project" not in kinds
    page = next(p for p in YearPlanner().pages(Spec(notes_pages=1)) if p.kind == "projects")
    assert any(isinstance(item, ProjectsBoard) for item in page.components)
    assert not any(isinstance(item, ProjectsIndexSpines) for item in page.components)
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Proj" not in texts
    assert "Atlas" not in texts
    assert "Shelf" not in texts


def test_projects_index_spines_page_and_leaves():
    spec = Spec(notes_pages=1)
    pages = _index_pages(spec)
    index = pages[0]
    assert index.dest == "projects-index-spines-2026"
    assert index.kind == "projects_index_spines"
    assert index.title == "Projects"
    board = next(item for item in index.components if isinstance(item, ProjectsIndexSpines))
    assert board.year == 2026
    assert board.index_dest == spec.projects_index_spines_dest
    assert len(board.spines) == 12
    assert board.spines[0].name == ""
    assert board.spines[0].dest == "project-2026-01"
    assert board.spines[0].hint == "01"
    assert board.spines[-1].name == ""
    assert board.spines[-1].dest == "project-2026-12"
    assert board.spines[-1].hint == "12"

    leaves = [p for p in pages if p.kind == "project"]
    assert len(leaves) == 12
    assert leaves[0].dest == "project-2026-01"
    assert leaves[0].title == "Project"
    leaf = next(item for item in leaves[0].components if isinstance(item, ProjectLeaf))
    assert leaf.index_dest == spec.projects_index_spines_dest
    assert leaf.hint == "01"
    assert leaf.tasks == 4
    board_one = next(item for item in leaves[0].components if isinstance(item, ProjectsBoard))
    assert board_one.cards == 1


def test_proj_tab_lands_on_index():
    spec = Spec(notes_pages=1)
    pages = _index_pages(spec)
    index = pages[0]
    assert strip_active(index.kind) == "Proj"
    assert strip_items(index) == (
        ("Year", "year-2026"),
        ("Proj", "projects-index-spines-2026"),
        ("Quar", "quarter-2026-Q1"),
        ("Mon", "month-2026-01"),
        ("Habit", "month-2026-01-habits"),
        ("Week", "week-2026-W01"),
        ("Day", "2026-01-01"),
        ("Notes", "2026-01-01-notes-1"),
    )
    leaf = pages[1]
    assert strip_active(leaf.kind) == "Proj"
    items = dict(strip_items(leaf))
    assert items["Proj"] == spec.projects_index_spines_dest


def test_default_strip_still_seven_tabs():
    page = next(p for p in YearPlanner().pages(Spec(notes_pages=1)) if p.kind == "projects")
    labels = [label for label, _ in strip_items(page)]
    assert labels == ["Year", "Quar", "Mon", "Habit", "Week", "Day", "Notes"]
    assert strip_active(page.kind) == ""


def test_spine_seats_two_centered_shelves():
    well = well_rect(NOMAD)
    assert projects_index_spine_row_count(12) == 2
    assert projects_index_spine_row_counts(12) == (6, 6)
    assert projects_index_spine_row_counts(10) == (5, 5)
    assert projects_index_spine_row_counts(9) == (5, 4)
    assert projects_index_spine_row_counts(8) == (4, 4)
    assert projects_index_spine_row_count(6) == 1
    assert projects_index_spine_row_counts(6) == (6,)

    shelves = projects_index_spine_shelves(well, 12)
    assert len(shelves) == 2
    assert shelves[0].y == pytest.approx(well.y)
    assert shelves[-1].bottom == pytest.approx(well.bottom)
    assert shelves[1].y - shelves[0].bottom == pytest.approx(INDEX_SPINE_ROW_GAP)
    assert shelves[0].h == pytest.approx(shelves[1].h)

    planks = projects_index_spine_planks(well, 12)
    assert len(planks) == 2
    assert planks[0].h == pytest.approx(INDEX_SPINE_PLANK)
    assert planks[0].bottom == pytest.approx(shelves[0].bottom)
    assert planks[0].w == pytest.approx(well.w)

    seats = projects_index_spine_seats(well, 12)
    assert len(seats) == 12
    top, bottom = seats[:6], seats[6:]
    assert top[0].y == pytest.approx(shelves[0].y + INDEX_SPINE_AIR)
    assert top[-1].bottom == pytest.approx(planks[0].y)
    assert bottom[0].y > top[-1].bottom
    for row in (top, bottom):
        assert row[0].x > well.x
        assert row[-1].right < well.right
        assert (row[0].x - well.x) == pytest.approx(well.right - row[-1].right)
        for seat in row:
            assert seat.w == pytest.approx(INDEX_SPINE_W)
        for earlier, later in zip(row, row[1:]):
            assert later.x - earlier.right == pytest.approx(INDEX_SPINE_GAP)


def test_paint_spines_writeins_and_links():
    spec = Spec(notes_pages=1)
    page = _index_pages(spec)[0]
    board = next(item for item in page.components if isinstance(item, ProjectsIndexSpines))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_projects_index_spines(plotter, well, board)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    for name in ("Atlas", "Beacon", "Tide", "Harbor", "Nomad", "Parch"):
        assert name not in texts
    letter_ops = [
        op
        for op in plotter.ops
        if op[0] == "text" and len(op[2]) == 1 and op[2].isalpha()
    ]
    assert letter_ops == []
    for spine in board.spines:
        assert spine.hint in texts
        assert spine.name == ""
    assert texts.count("01") == 1
    assert texts.count("12") == 1
    assert "Todo" not in texts
    assert "Doing" not in texts
    assert "Done" not in texts
    assert "PROJECT" not in texts
    assert "Focus" not in texts

    seats = projects_index_spine_seats(well, 12)
    writeins = 0
    for seat in seats:
        foot_top = seat.bottom - INDEX_SPINE_FOOT_H
        well_title = Rect(
            seat.x, seat.y + INDEX_SPINE_HEAD, seat.w, foot_top - seat.y - INDEX_SPINE_HEAD
        )
        marks = projects_index_spine_writeins(well_title)
        assert len(marks) >= 4
        writeins += len(marks)
    rules = [
        op
        for op in plotter.ops
        if op[0] == "line" and op[5] == pytest.approx(RULE_C)
    ]
    assert len(rules) == writeins

    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert ticks == []
    p_boxes = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(PROJECT_P)
    ]
    assert p_boxes == []

    links = plotter.links()
    assert links == [spine.dest for spine in board.spines]
    assert spec.projects_index_spines_dest not in links
    for op in plotter.ops:
        if op[0] == "link":
            assert op[1].w == pytest.approx(INDEX_SPINE_W)
            assert op[1].x > well.x


def test_spine_open_frames_and_headcaps():
    spec = Spec(notes_pages=1)
    page = _index_pages(spec)[0]
    board = next(item for item in page.components if isinstance(item, ProjectsIndexSpines))
    plotter = RecordingPlotter()
    paint_projects_index_spines(plotter, well_rect(NOMAD), board)

    ink_fills = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[3] and op[5] == pytest.approx(0.0)
    ]
    dark_spines = [op for op in ink_fills if op[1].w == pytest.approx(INDEX_SPINE_W) and op[1].h > 20]
    headcaps = [
        op
        for op in ink_fills
        if op[1].w == pytest.approx(INDEX_SPINE_W) and op[1].h == pytest.approx(INDEX_SPINE_HEAD)
    ]
    assert dark_spines == []
    assert len(headcaps) == 12
    frames = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[2]
        and not op[3]
        and op[1].w == pytest.approx(INDEX_SPINE_W)
    ]
    assert len(frames) == 12
    planks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[3] and op[1].h == pytest.approx(INDEX_SPINE_PLANK)
    ]
    assert len(planks) == 2


def test_index_spines_knob():
    spec = Spec(notes_pages=1, project_index_spines=8)
    catalog = spine_catalog(spec)
    assert len(catalog) == 8
    assert catalog[-1].name == ""
    assert catalog[-1].dest == "project-2026-08"
    seats = projects_index_spine_seats(well_rect(NOMAD), 8)
    assert len(seats) == 8
    assert projects_index_spine_row_counts(8) == (4, 4)


def test_index_and_leaves_link_both_ways():
    spec = Spec(notes_pages=1)
    pages = _index_pages(spec)
    plotter = RecordingPlotter()
    for page in pages:
        plotter.reserve_dest(page.dest)
    for page in pages:
        plotter.begin_page()
        plotter.add_dest(page.dest)
        PlannerLayout().paint(page, plotter, NOMAD)

    dests = plotter.dests()
    assert dests[0] == spec.projects_index_spines_dest
    assert "project-2026-01" in dests
    assert "project-2026-12" in dests

    links = plotter.links()
    for spine in spine_catalog(spec):
        assert spine.dest in links
    assert links.count(spec.projects_index_spines_dest) >= 12

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Projects" in texts
    assert "Shelf" in texts
    assert "Index" in texts
    assert texts.count("Proj") >= 2
    assert "Atlas" not in texts
    assert "Project" in texts


def test_project_leaf_reuses_card_craft():
    spec = Spec(notes_pages=1)
    page = next(p for p in _index_pages(spec) if p.dest == "project-2026-01")
    board = next(item for item in page.components if isinstance(item, ProjectsBoard))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_project(plotter, well, board)
    frames = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(well.w)
    ]
    assert len(frames) == 1
    assert frames[0][1].h == pytest.approx(project_card_seats(well, 3)[0].h)
    assert frames[0][1].h < well.h * 0.5
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
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


def test_index_spines_header_and_proj_active():
    spec = Spec(notes_pages=1)
    page = _index_pages(spec)[0]
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Projects" in texts
    assert "Shelf" in texts
    assert "Proj" in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Week", "Day", "Notes"):
        assert label in texts
    assert strip_active(page.kind) == "Proj"
    assert plotter.links().count("project-2026-01") == 1
    assert spec.projects_index_spines_dest in plotter.links()
