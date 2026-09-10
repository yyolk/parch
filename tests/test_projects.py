import pytest

from parch.books import YearPlanner
from parch.components import ProjectsBoard
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    PROJECT_COL_WEIGHTS,
    PROJECT_P,
    PROJECT_STATUS_H,
    PROJECT_STATUS_MARK,
    RULE,
    STATUS_STRIP_HEAD_H,
    TICK,
    WASH,
    paint_projects,
    paint_projects_status_strips,
    project_card_columns,
    project_card_left_seats,
    project_card_seats,
    project_status_strip_legend_slots,
    project_status_strip_name_box,
    project_status_strip_name_rows,
    project_status_strip_seats,
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


def test_project_status_strip_tracks():
    well = Rect(4, 20, 110, 90)
    legend, lanes = project_status_strip_seats(well)
    assert legend.y == pytest.approx(well.y)
    assert legend.x == pytest.approx(well.x)
    assert legend.w == pytest.approx(well.w)
    assert legend.h == pytest.approx(STATUS_STRIP_HEAD_H)
    assert len(lanes) == 3
    assert lanes[0].y == pytest.approx(legend.bottom)
    assert lanes[0].x == pytest.approx(well.x)
    assert lanes[-1].right == pytest.approx(well.right)
    assert lanes[-1].bottom == pytest.approx(well.bottom)
    assert lanes[1].x == pytest.approx(lanes[0].right)
    assert lanes[2].x == pytest.approx(lanes[1].right)
    assert all(lane.w == pytest.approx(well.w / 3) for lane in lanes)

    slots = project_status_strip_legend_slots(legend)
    assert [slot.x for slot in slots] == [pytest.approx(lane.x) for lane in lanes]
    assert [slot.w for slot in slots] == [pytest.approx(lane.w) for lane in lanes]

    names = project_status_strip_name_rows(lanes[0])
    assert len(names) >= 8
    assert names[0].y == pytest.approx(lanes[0].y)
    assert names[-1].bottom == pytest.approx(lanes[0].bottom)
    assert names[0].x == pytest.approx(lanes[0].x)


def test_projects_status_strips_paint_legend_and_name_lines():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "projects")
    board = next(item for item in page.components if isinstance(item, ProjectsBoard))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_projects_status_strips(plotter, well, board)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("Todo") == 1
    assert texts.count("Doing") == 1
    assert texts.count("Done") == 1
    assert "P" not in texts
    assert "Focus" not in texts
    assert "Notes" not in texts
    assert "PROJECT" not in texts

    legend, lanes = project_status_strip_seats(well)
    marks = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[2]
        and not op[3]
        and op[1].w == pytest.approx(PROJECT_STATUS_MARK)
    ]
    assert len(marks) == 3
    for op in marks:
        assert op[1].y + op[1].h <= legend.bottom + 0.01

    expected = 3 * len(project_status_strip_name_rows(project_status_strip_name_box(lanes[0])))
    name_rules = [op for op in plotter.ops if op[0] == "line" and op[5] == pytest.approx(RULE)]
    assert len(name_rules) == expected
    assert expected > board.cards * board.tasks
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert ticks == []

    washes = [op for op in plotter.ops if op[0] == "rect" and op[3] and not op[2]]
    assert len(washes) == 1
    assert washes[0][1].h == pytest.approx(legend.h)
    assert washes[0][5] == pytest.approx(WASH)

    p_boxes = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(PROJECT_P)
    ]
    assert p_boxes == []


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
