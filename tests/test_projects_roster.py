"""Thesis B — dense roster. Parallel to the stacked 3-card Projects page."""

import pytest

from parch.books import YearPlanner
from parch.components import ROSTER_ROWS, ProjectsBoard, ProjectsRoster
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    PROJECT_P,
    PROJECT_STATUS_MARK,
    ROSTER_ROW_GAP,
    TICK,
    paint_projects_dense,
    roster_row_bands,
    roster_row_seats,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.sections import ProjectsRosterSection
from parch.spec import Spec


def test_roster_stays_out_of_the_default_book():
    pages = YearPlanner().pages(Spec(notes_pages=1))
    assert pages[2].kind == "projects"
    assert pages[2].dest == "projects-2026"
    board = next(item for item in pages[2].components if isinstance(item, ProjectsBoard))
    assert board.cards == 3
    assert not any(page.kind == "projects_roster" for page in pages)
    assert "projects-roster-2026" not in [page.dest for page in pages]


def test_roster_section_page():
    spec = Spec(notes_pages=1)
    page = ProjectsRosterSection(spec).pages()[0]
    assert page.dest == "projects-roster-2026"
    assert page.kind == "projects_roster"
    assert page.title == "Projects"
    roster = next(item for item in page.components if isinstance(item, ProjectsRoster))
    assert roster.year == 2026
    assert roster.rows == ROSTER_ROWS == 8
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


def test_roster_row_tracks():
    well = well_rect(NOMAD)
    seats = roster_row_seats(well, ROSTER_ROWS)
    assert len(seats) == 8
    assert seats[0].y == pytest.approx(well.y)
    assert seats[0].x == pytest.approx(well.x)
    assert seats[0].w == pytest.approx(well.w)
    assert seats[-1].bottom == pytest.approx(well.bottom)
    for earlier, later in zip(seats[:-1], seats[1:], strict=True):
        assert later.y > earlier.bottom
    # Writable floor: name line + 3.2 mm status marks still fit.
    assert seats[0].h == pytest.approx((well.h - ROSTER_ROW_GAP * 7) / 8)
    assert seats[0].h >= 14.0

    header, status = roster_row_bands(seats[0])
    assert header.y > seats[0].y
    assert header.x > seats[0].x
    assert status.y > header.bottom
    assert status.bottom < seats[0].bottom
    assert header.right == pytest.approx(status.right)
    assert status.h >= PROJECT_STATUS_MARK


def test_roster_paint_has_no_tasks_or_notes():
    spec = Spec(notes_pages=1)
    page = ProjectsRosterSection(spec).pages()[0]
    roster = next(item for item in page.components if isinstance(item, ProjectsRoster))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_projects_dense(plotter, well, roster)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("P") == 8
    assert texts.count("Todo") == 8
    assert texts.count("Doing") == 8
    assert texts.count("Done") == 8
    assert "PROJECT" not in texts
    assert "Focus" not in texts
    assert "Notes" not in texts

    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert ticks == []

    marks = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[2]
        and not op[3]
        and op[1].w == pytest.approx(PROJECT_STATUS_MARK)
    ]
    assert len(marks) == 8 * 3

    p_boxes = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(PROJECT_P)
    ]
    assert len(p_boxes) == 8

    outlines = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(well.w)
    ]
    assert len(outlines) == 8

    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []


def test_roster_header_year_and_seven_tabs():
    spec = Spec(notes_pages=1)
    page = ProjectsRosterSection(spec).pages()[0]
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Projects" in texts
    assert "2026" in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Week", "Day", "Notes"):
        assert label in texts


def test_roster_rows_knob():
    plotter = RecordingPlotter()
    paint_projects_dense(plotter, Rect(4, 20, 110, 90), ProjectsRoster(year=2026, rows=6))
    assert [op[2] for op in plotter.ops if op[0] == "text"].count("P") == 6
    assert [op[2] for op in plotter.ops if op[0] == "text"].count("Todo") == 6
