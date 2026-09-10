import pytest

from parch.books import YearPlanner
from parch.components import ProjectsBoard
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    CLONE_RAIL_W,
    CLONE_STATUS_RAIL_W,
    CLONE_TRACK_MARK,
    HABIT_WASH,
    INK,
    PAPER,
    PROJECT_COL_WEIGHTS,
    PROJECT_P,
    PROJECT_STATUS_H,
    PROJECT_STATUS_MARK,
    TICK,
    WASH,
    clone_craft_body,
    clone_craft_columns,
    clone_craft_left,
    clone_craft_rail,
    clone_craft_seats,
    clone_craft_shell,
    clone_craft_status_rail,
    paint_projects,
    paint_projects_clone_craft,
    project_card_columns,
    project_card_left_seats,
    project_card_seats,
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
    assert pages[3].dest == "quarter-2026-Q1"

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


def test_projects_header_year_and_seven_tabs():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "projects")
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Projects" in texts
    assert "2026" in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Week", "Day", "Notes"):
        assert label in texts


def test_clone_craft_seats_rail_and_status_track():
    well = Rect(4, 20, 110, 90)
    cards = clone_craft_seats(well, 3)
    assert len(cards) == 3
    assert cards[0].y == pytest.approx(well.y)
    assert cards[0].w == pytest.approx(well.w)
    assert cards[-1].bottom == pytest.approx(well.bottom)
    assert cards[1].y > cards[0].bottom

    rail, body, status = clone_craft_shell(cards[0])
    assert rail == clone_craft_rail(cards[0])
    assert body == clone_craft_body(cards[0])
    assert status == clone_craft_status_rail(cards[0])
    assert rail.w == pytest.approx(CLONE_RAIL_W)
    assert rail.x == pytest.approx(cards[0].x)
    assert rail.h == pytest.approx(cards[0].h)
    assert body.x == pytest.approx(rail.right)
    assert status.w == pytest.approx(CLONE_STATUS_RAIL_W)
    assert status.x == pytest.approx(body.right)
    assert status.right == pytest.approx(cards[0].right)
    assert status.h == pytest.approx(cards[0].h)
    assert body.w == pytest.approx(cards[0].w - CLONE_RAIL_W - CLONE_STATUS_RAIL_W)

    left, notes = clone_craft_columns(body)
    assert left.x > body.x
    assert notes.right < body.right
    assert left.right < notes.x
    assert notes.w > left.w
    assert notes.right < status.x

    header, tasks = clone_craft_left(left)
    assert header.y == pytest.approx(left.y)
    assert tasks.y > header.bottom
    assert tasks.bottom == pytest.approx(left.bottom)


def test_clone_craft_paint_uses_nomad_ink():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "projects")
    board = next(item for item in page.components if isinstance(item, ProjectsBoard))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_projects_clone_craft(plotter, well, board)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("P") == 3
    assert texts.count("Todo") == 3
    assert texts.count("Doing") == 3
    assert texts.count("Done") == 3
    assert "PROJECT" not in texts
    assert "TO DO" not in texts
    assert "IN PROGRESS" not in texts
    assert "DONE!" not in texts
    assert "Focus" not in texts
    assert "Notes" not in texts

    rails = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[3]
        and not op[2]
        and op[1].w == pytest.approx(CLONE_RAIL_W)
        and op[5] == pytest.approx(INK)
    ]
    assert len(rails) == 3

    inverted = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[3]
        and not op[2]
        and op[1].w == pytest.approx(PROJECT_P)
        and op[5] == pytest.approx(INK)
    ]
    assert len(inverted) == 3
    p_ink = [op for op in plotter.ops if op[0] == "text" and op[2] == "P"]
    assert all(op[7] == pytest.approx(PAPER) for op in p_ink)

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
        and op[3]
        and op[1].w == pytest.approx(CLONE_TRACK_MARK)
        and op[5] == pytest.approx(PAPER)
    ]
    assert len(marks) == 9

    zebra = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[3] and not op[2] and op[5] == pytest.approx(HABIT_WASH)
    ]
    assert len(zebra) == 3 * 2

    bands = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[3]
        and not op[2]
        and op[5] == pytest.approx(WASH)
        and op[1].w == pytest.approx(CLONE_STATUS_RAIL_W)
    ]
    assert len(bands) == 3


def test_clone_craft_does_not_replace_default_paint():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "projects")
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    rails = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[3]
        and not op[2]
        and op[1].w == pytest.approx(CLONE_RAIL_W)
    ]
    assert rails == []
