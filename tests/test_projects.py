import pytest

from parch.books import YearPlanner
from parch.components import ProjectPage, ProjectsBoard, ProjectsIndex
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    INDEX_FOCUS_GAP,
    INDEX_FOCUS_WEIGHTS,
    INDEX_LIST_MARK,
    INDEX_LIST_P,
    PROJECT_COL_WEIGHTS,
    PROJECT_P,
    PROJECT_STATUS_H,
    PROJECT_STATUS_MARK,
    TICK,
    paint_project,
    paint_projects,
    paint_projects_index_focus,
    project_card_columns,
    project_card_left_seats,
    project_card_seats,
    projects_index_focus_seats,
    projects_index_focus_strip,
    projects_index_list_row,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.spec import Spec


def test_projects_page_after_annual():
    spec = Spec(notes_pages=1)
    pages = YearPlanner().pages(spec)
    assert pages[1].dest == "year-2026"
    page = pages[2]
    assert page.dest == "projects-2026"
    assert page.kind == "projects"
    assert page.title == "Projects"
    assert pages[3].dest == "projects-index-2026"
    assert pages[12].dest == "quarter-2026-Q1"

    board = next(item for item in page.components if isinstance(item, ProjectsBoard))
    assert board.year == 2026
    assert board.cards == 3
    assert board.tasks == 4

    assert strip_active(page.kind) == ""
    assert strip_items(page) == (
        ("Year", "year-2026"),
        ("Quar", "quarter-2026-Q1"),
        ("Mon", "month-2026-01"),
        ("Habit", "month-2026-01-habits"),
        ("Proj", "projects-index-2026"),
        ("Week", "week-2026-W01"),
        ("Day", "2026-01-01"),
        ("Notes", "2026-01-01-notes-1"),
    )


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
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "projects")
    board = next(item for item in page.components if isinstance(item, ProjectsBoard))
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
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "projects")
    board = next(item for item in page.components if isinstance(item, ProjectsBoard))
    assert board.cards == 2
    assert board.tasks == 5
    plotter = RecordingPlotter()
    paint_projects(plotter, Rect(4, 20, 110, 90), board)
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
    for label in ("Year", "Quar", "Mon", "Habit", "Proj", "Week", "Day", "Notes"):
        assert label in texts


def test_projects_index_after_board_and_proj_nav():
    spec = Spec(notes_pages=1)
    pages = YearPlanner().pages(spec)
    dests = [page.dest for page in pages]
    assert dests[2] == "projects-2026"
    assert dests[3] == "projects-index-2026"
    assert dests[4:12] == [f"project-2026-{slot:02d}" for slot in range(1, 9)]
    assert dests[12] == "quarter-2026-Q1"

    index = pages[3]
    assert index.kind == "projects_index"
    assert index.title == "Projects"
    assert strip_active(index.kind) == "Proj"
    assert strip_items(index) == (
        ("Year", "year-2026"),
        ("Quar", "quarter-2026-Q1"),
        ("Mon", "month-2026-01"),
        ("Habit", "month-2026-01-habits"),
        ("Proj", "projects-index-2026"),
        ("Week", "week-2026-W01"),
        ("Day", "2026-01-01"),
        ("Notes", "2026-01-01-notes-1"),
    )

    roster = next(item for item in index.components if isinstance(item, ProjectsIndex))
    assert roster.year == 2026
    assert roster.dest == "projects-index-2026"
    assert roster.featured == "project-2026-01"
    assert roster.entries == tuple(f"project-2026-{slot:02d}" for slot in range(2, 9))

    leaf = next(page for page in pages if page.dest == "project-2026-03")
    assert leaf.kind == "project"
    assert leaf.title == "Project"
    assert strip_active(leaf.kind) == "Proj"
    assert ("Proj", "projects-index-2026") in strip_items(leaf)
    card = next(item for item in leaf.components if isinstance(item, ProjectPage))
    assert card.slot == 3
    assert card.dest == "project-2026-03"
    assert card.index_dest == "projects-index-2026"
    assert card.tasks == 4


def test_projects_index_focus_seats():
    well = Rect(4, 20, 110, 90)
    focus, listing = projects_index_focus_seats(well, 7)
    assert focus.x == pytest.approx(well.x)
    assert focus.y == pytest.approx(well.y)
    assert focus.w == pytest.approx(well.w)
    assert listing[0].y > focus.bottom
    assert listing[-1].bottom == pytest.approx(well.bottom)
    assert len(listing) == 7
    leftover = well.h - INDEX_FOCUS_GAP
    assert focus.h == pytest.approx(leftover * INDEX_FOCUS_WEIGHTS[0] / sum(INDEX_FOCUS_WEIGHTS))
    band_h = leftover * INDEX_FOCUS_WEIGHTS[1] / sum(INDEX_FOCUS_WEIGHTS)
    assert listing[-1].bottom - listing[0].y == pytest.approx(band_h)

    name, status = projects_index_focus_strip(focus)
    assert name.x > focus.x
    assert status.right < focus.right
    assert name.right < status.x
    assert status.w == pytest.approx(42.0)

    row_name, marks = projects_index_list_row(listing[0])
    assert row_name.x > listing[0].x
    assert marks.right < listing[0].right
    assert row_name.right < marks.x


def test_projects_index_focus_paint_links():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "projects_index")
    roster = next(item for item in page.components if isinstance(item, ProjectsIndex))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_projects_index_focus(plotter, well, roster)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("P") == 8
    assert texts.count("Todo") == 1
    assert texts.count("Doing") == 1
    assert texts.count("Done") == 1
    assert "PROJECT" not in texts
    assert "Focus" not in texts
    assert "Notes" not in texts

    p_hero = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(PROJECT_P)
    ]
    assert len(p_hero) == 1
    p_list = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(INDEX_LIST_P)
    ]
    assert len(p_list) == 7

    hero_marks = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[2]
        and not op[3]
        and op[1].w == pytest.approx(PROJECT_STATUS_MARK)
    ]
    assert len(hero_marks) == 3
    list_marks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(INDEX_LIST_MARK)
    ]
    assert len(list_marks) == 21

    links = [op[2] for op in plotter.ops if op[0] == "link"]
    assert links[0] == "project-2026-01"
    assert links[1:] == [f"project-2026-{slot:02d}" for slot in range(2, 9)]
    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []


def test_project_page_card_and_index_chip():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.dest == "project-2026-01")
    card = next(item for item in page.components if isinstance(item, ProjectPage))
    well = well_rect(NOMAD)
    ink = RecordingPlotter()
    paint_project(ink, well, card)
    texts = [op[2] for op in ink.ops if op[0] == "text"]
    assert texts.count("P") == 1
    assert texts.count("Todo") == 1
    ticks = [
        op
        for op in ink.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 4

    chrome = RecordingPlotter()
    chrome.begin_page()
    PlannerLayout().paint(page, chrome, NOMAD)
    labels = [op[2] for op in chrome.ops if op[0] == "text"]
    assert "Project" in labels
    assert "Index" in labels
    assert "Proj" in labels
    chip_links = [op[2] for op in chrome.ops if op[0] == "link" and op[2] == "projects-index-2026"]
    assert chip_links


def test_projects_index_rows_knob():
    spec = Spec(notes_pages=1, project_index_rows=6)
    pages = YearPlanner().pages(spec)
    roster = next(
        item
        for page in pages
        if page.kind == "projects_index"
        for item in page.components
        if isinstance(item, ProjectsIndex)
    )
    assert len(roster.entries) == 6
    dests = [page.dest for page in pages]
    assert "project-2026-07" in dests
    assert "project-2026-08" not in dests
    plotter = RecordingPlotter()
    paint_projects_index_focus(plotter, Rect(4, 20, 110, 90), roster)
    assert [op[2] for op in plotter.ops if op[0] == "text"].count("P") == 7
