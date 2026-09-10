import pytest

from parch.books import YearPlanner
from parch.components import ProjectsBoard, ProjectsWaiting
from parch.devices.nomad import NOMAD
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    HAIR,
    PROJECT_P,
    PROJECT_STATUS_MARK,
    RULE,
    RULE_C,
    TICK,
    WAIT_BAND_GAP,
    WAIT_INSET_X,
    WAIT_INSET_Y,
    WAIT_LABEL_GAP,
    WAIT_LABEL_H,
    WAIT_NAME_H,
    WAIT_NOTES_LINES,
    WAIT_ROW_GAP,
    WAIT_WHO_GAP,
    WAIT_WHO_H,
    paint_projects_waiting,
    projects_waiting_band_seats,
    projects_waiting_notes_seats,
    projects_waiting_row_seats,
    projects_waiting_seats,
    strip_active,
    strip_items,
    waiting_notes_height,
    waiting_row_height,
)
from parch.plotter import RecordingPlotter
from parch.sections.projects_waiting import ProjectsWaitingSection
from parch.spec import Spec


def test_projects_waiting_not_in_year_book():
    kinds = [page.kind for page in YearPlanner().pages(Spec(notes_pages=1))]
    assert kinds.count("projects") == 1
    assert "projects_waiting" not in kinds
    page = next(p for p in YearPlanner().pages(Spec(notes_pages=1)) if p.kind == "projects")
    assert any(isinstance(item, ProjectsBoard) for item in page.components)
    assert not any(isinstance(item, ProjectsWaiting) for item in page.components)


def test_projects_waiting_page():
    spec = Spec(notes_pages=1)
    page = ProjectsWaitingSection(spec).pages()[0]
    assert page.dest == "projects-waiting-2026"
    assert page.kind == "projects_waiting"
    assert page.title == "Projects"
    board = next(item for item in page.components if isinstance(item, ProjectsWaiting))
    assert board.year == 2026
    assert board.rows == 3
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


def test_projects_waiting_seats_three_bands():
    well = well_rect(NOMAD)
    bands, notes = projects_waiting_seats(well, 3)
    assert len(bands) == 3
    assert bands[0].y == pytest.approx(well.y)
    assert bands[0].x == pytest.approx(well.x)
    assert bands[0].w == pytest.approx(well.w)
    assert bands[1].y == pytest.approx(bands[0].bottom + WAIT_BAND_GAP)
    assert bands[2].y == pytest.approx(bands[1].bottom + WAIT_BAND_GAP)
    assert bands[0].h == pytest.approx(bands[1].h)
    assert bands[1].h == pytest.approx(bands[2].h)
    assert notes.h == pytest.approx(waiting_notes_height())
    assert notes.y == pytest.approx(bands[2].bottom + WAIT_BAND_GAP)
    assert notes.bottom == pytest.approx(well.bottom)
    assert notes.x == pytest.approx(well.x)
    assert notes.w == pytest.approx(well.w)

    moving_label, moving_rows = projects_waiting_band_seats(bands[0], 3, stuck=False)
    assert moving_label.y == pytest.approx(bands[0].y + WAIT_INSET_Y)
    assert moving_label.h == pytest.approx(WAIT_LABEL_H)
    assert moving_label.x == pytest.approx(bands[0].x + WAIT_INSET_X)
    assert len(moving_rows) == 3
    assert moving_rows[0].y == pytest.approx(moving_label.bottom + WAIT_LABEL_GAP)
    assert moving_rows[1].y == pytest.approx(moving_rows[0].bottom + WAIT_ROW_GAP)
    assert moving_rows[0].h == pytest.approx(waiting_row_height(stuck=False))
    assert moving_rows[-1].bottom < bands[0].bottom - WAIT_INSET_Y + 0.01

    waiting_label, waiting_rows = projects_waiting_band_seats(bands[1], 3, stuck=True)
    assert waiting_label.h == pytest.approx(WAIT_LABEL_H)
    assert len(waiting_rows) == 3
    assert waiting_rows[0].h == pytest.approx(waiting_row_height(stuck=True))
    assert waiting_rows[-1].bottom < bands[1].bottom - WAIT_INSET_Y + 0.01

    name, who = projects_waiting_row_seats(moving_rows[0], stuck=False)
    assert name.h == pytest.approx(WAIT_NAME_H)
    assert who is None

    name, who = projects_waiting_row_seats(waiting_rows[0], stuck=True)
    assert name.h == pytest.approx(WAIT_NAME_H)
    assert who is not None
    assert who.y == pytest.approx(name.bottom + WAIT_WHO_GAP)
    assert who.h == pytest.approx(WAIT_WHO_H)
    assert who.bottom == pytest.approx(waiting_rows[0].bottom)

    note_label, note_lines = projects_waiting_notes_seats(notes)
    assert note_label.y == pytest.approx(notes.y)
    assert note_label.h == pytest.approx(WAIT_LABEL_H)
    assert note_lines.y > note_label.bottom
    assert note_lines.bottom == pytest.approx(notes.bottom)


def test_projects_waiting_paint_ticks_who_and_notes():
    board = ProjectsWaiting(year=2026, rows=3)
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_projects_waiting(plotter, well, board)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("Moving") == 1
    assert texts.count("Waiting on…") == 1
    assert texts.count("Blocked") == 1
    assert texts.count("Next unblock") == 1
    for rejected in (
        "P",
        "Todo",
        "Doing",
        "Done",
        "Focus",
        "Notes",
        "PROJECT",
        "TO DO",
        "IN PROGRESS",
        "DONE!",
        "Parking lot",
        "Active",
        "Meeting",
    ):
        assert rejected not in texts

    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 3 * 3

    p_boxes = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(PROJECT_P)
    ]
    assert p_boxes == []

    marks = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[2]
        and not op[3]
        and op[1].w == pytest.approx(PROJECT_STATUS_MARK)
    ]
    assert marks == []

    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []

    band_outlines = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[2]
        and not op[3]
        and op[1].w == pytest.approx(well.w)
    ]
    assert len(band_outlines) == 3

    name_and_who = [
        op
        for op in plotter.ops
        if op[0] == "line"
        and op[5] == pytest.approx(RULE)
        and op[6] == pytest.approx(RULE_C)
        and op[3] - op[1] == pytest.approx(well.w - 2 * WAIT_INSET_X - TICK - 1.4)
    ]
    # 9 name underlines + 6 who/what underlines (Waiting + Blocked)
    assert len(name_and_who) == 9 + 6

    note_rules = [
        op
        for op in plotter.ops
        if op[0] == "line"
        and op[5] == pytest.approx(RULE)
        and op[6] == pytest.approx(RULE_C)
        and op[3] - op[1] == pytest.approx(well.w)
    ]
    assert len(note_rules) == WAIT_NOTES_LINES

    seps = [
        op
        for op in plotter.ops
        if op[0] == "line" and op[5] == pytest.approx(HAIR) and op[3] - op[1] == pytest.approx(well.w)
    ]
    assert seps == []


def test_projects_waiting_knobs():
    spec = Spec(notes_pages=1, project_waiting_rows=2)
    page = ProjectsWaitingSection(spec).pages()[0]
    board = next(item for item in page.components if isinstance(item, ProjectsWaiting))
    assert board.rows == 2
    well = well_rect(NOMAD)
    bands, _notes = projects_waiting_seats(well, board.rows)
    _, waiting_rows = projects_waiting_band_seats(bands[1], board.rows, stuck=True)
    assert len(waiting_rows) == 2
    assert waiting_rows[-1].bottom < bands[1].bottom - WAIT_INSET_Y + 0.01
    plotter = RecordingPlotter()
    paint_projects_waiting(plotter, well, board)
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 3 * 2
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("Moving") == 1
    assert texts.count("Waiting on…") == 1
    assert texts.count("Blocked") == 1


def test_projects_waiting_header_year_and_seven_tabs():
    spec = Spec(notes_pages=1)
    page = ProjectsWaitingSection(spec).pages()[0]
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Projects" in texts
    assert "2026" in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Week", "Day", "Notes"):
        assert label in texts
    assert "Projects" == page.title
