import pytest

from parch.books import YearPlanner
from parch.components import ProjectsBoard, ProjectsParking
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    FOCUS_PITCH,
    PARKING_COL_GAP,
    PARKING_COL_WEIGHTS,
    PARKING_LABEL_GAP,
    PARKING_LABEL_H,
    PARKING_LINE_H,
    PARKING_LOT_INSET_Y,
    PROJECT_P,
    PROJECT_STATUS_H,
    PROJECT_STATUS_MARK,
    TICK,
    paint_projects,
    paint_projects_parking,
    parking_lot_well_height,
    parking_task_band_height,
    projects_parking_active_seats,
    projects_parking_card_seats,
    projects_parking_lot_seats,
    projects_parking_seats,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.sections.projects_parking import ACTIVE_TASKS, LOT_ROWS, ProjectsParkingSection
from parch.spec import Spec


def test_projects_parking_not_in_year_book():
    kinds = [page.kind for page in YearPlanner().pages(Spec(notes_pages=1))]
    assert kinds.count("projects") == 1
    assert "projects_parking" not in kinds
    page = next(p for p in YearPlanner().pages(Spec(notes_pages=1)) if p.kind == "projects")
    assert any(isinstance(item, ProjectsBoard) for item in page.components)
    assert not any(isinstance(item, ProjectsParking) for item in page.components)


def test_projects_parking_page():
    spec = Spec(notes_pages=1)
    page = ProjectsParkingSection(spec).pages()[0]
    assert page.dest == "projects-parking-2026"
    assert page.kind == "projects_parking"
    assert page.title == "Projects"
    board = next(item for item in page.components if isinstance(item, ProjectsParking))
    assert board.year == 2026
    assert board.lot_rows == 8
    assert board.tasks == 5
    assert LOT_ROWS == 8
    assert ACTIVE_TASKS == 5
    assert 6 <= LOT_ROWS <= 8
    assert 4 <= ACTIVE_TASKS <= 5
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


def test_projects_parking_seats_lot_left_active_right():
    well = well_rect(NOMAD)
    lot, active = projects_parking_seats(well)
    assert lot.x == pytest.approx(well.x)
    assert lot.y == pytest.approx(well.y)
    assert lot.bottom == pytest.approx(well.bottom)
    assert active.right == pytest.approx(well.right)
    assert active.y == pytest.approx(well.y)
    assert active.bottom == pytest.approx(well.bottom)
    assert active.x == pytest.approx(lot.right + PARKING_COL_GAP)
    share = lot.w + active.w
    assert lot.w / share == pytest.approx(PARKING_COL_WEIGHTS[0] / sum(PARKING_COL_WEIGHTS))
    assert active.w / share == pytest.approx(PARKING_COL_WEIGHTS[1] / sum(PARKING_COL_WEIGHTS))
    assert lot.w < active.w

    label, inbox, lines = projects_parking_lot_seats(lot, 8)
    assert label.y == pytest.approx(lot.y)
    assert label.h == pytest.approx(PARKING_LABEL_H)
    assert inbox.y == pytest.approx(label.bottom + PARKING_LABEL_GAP)
    assert inbox.h == pytest.approx(parking_lot_well_height(8))
    assert inbox.bottom < lot.bottom
    assert len(lines) == 8
    assert lines[0].y == pytest.approx(inbox.y + PARKING_LOT_INSET_Y)
    assert lines[-1].bottom == pytest.approx(inbox.bottom - PARKING_LOT_INSET_Y)
    assert lines[1].y > lines[0].bottom
    assert lines[0].h == pytest.approx(PARKING_LINE_H)

    zone, card = projects_parking_active_seats(active)
    assert zone.y == pytest.approx(active.y)
    assert zone.h == pytest.approx(PARKING_LABEL_H)
    assert card.y == pytest.approx(zone.bottom + PARKING_LABEL_GAP)
    assert card.bottom == pytest.approx(active.bottom)
    assert card.w == pytest.approx(active.w)

    header, tasks, status, notes = projects_parking_card_seats(card, 5)
    assert header.y > card.y
    assert tasks.y > header.bottom
    assert status.y > tasks.bottom
    assert notes.y > status.bottom
    assert notes.bottom < card.bottom
    assert tasks.h == pytest.approx(parking_task_band_height(5))
    assert status.h == pytest.approx(PROJECT_STATUS_H)
    assert notes.h > tasks.h
    assert parking_task_band_height(5) == pytest.approx(0.4 + TICK + 4 * FOCUS_PITCH)


def test_projects_parking_paint_underlines_card_ticks_status():
    board = ProjectsParking(year=2026, lot_rows=8, tasks=5)
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_projects_parking(plotter, well, board)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("Parking lot") == 1
    assert texts.count("Active") == 1
    assert texts.count("P") == 1
    assert texts.count("Todo") == 1
    assert texts.count("Doing") == 1
    assert texts.count("Done") == 1
    assert "Focus" not in texts
    assert "Notes" not in texts
    assert "PROJECT" not in texts
    for rejected in ("TO DO", "IN PROGRESS", "DONE!", "Week", "Month", "Someday"):
        assert rejected not in texts

    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 5

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

    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []

    lot, active = projects_parking_seats(well)
    _, card = projects_parking_active_seats(active)
    _, inbox, lines = projects_parking_lot_seats(lot, 8)
    outlines = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[2]
        and not op[3]
        and (
            op[1].w == pytest.approx(card.w, abs=0.01)
            or op[1].w == pytest.approx(inbox.w, abs=0.01)
        )
    ]
    assert len(outlines) == 2

    name_rules = [
        op
        for op in plotter.ops
        if op[0] == "line"
        and op[1] == pytest.approx(lines[0].x)
        and op[3] == pytest.approx(lines[0].right)
        and op[2] >= lines[0].y - 0.05
    ]
    assert len(name_rules) == 8


def test_projects_parking_knobs():
    board = ProjectsParking(year=2026, lot_rows=6, tasks=4)
    plotter = RecordingPlotter()
    paint_projects_parking(plotter, Rect(4, 20, 110, 90), board)
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 4
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("P") == 1
    assert texts.count("Parking lot") == 1
    assert texts.count("Active") == 1


def test_default_projects_unchanged_by_parking():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "projects")
    board = next(item for item in page.components if isinstance(item, ProjectsBoard))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_projects(plotter, well, board)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("P") == 3
    assert "Parking lot" not in texts
    assert "Active" not in texts


def test_projects_parking_header_year_and_seven_tabs():
    spec = Spec(notes_pages=1)
    page = ProjectsParkingSection(spec).pages()[0]
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Projects" in texts
    assert "2026" in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Week", "Day", "Notes"):
        assert label in texts
    assert "Parking lot" in texts
    assert "Active" in texts
