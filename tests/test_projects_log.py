import pytest

from parch.books import YearPlanner
from parch.components import ProjectsBoard, ProjectsLog
from parch.devices.nomad import NOMAD
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    HAIR,
    LOG_BODY_GAP,
    LOG_DATE_W,
    LOG_ENTRY_GAP,
    LOG_HEAD_H,
    LOG_LINE_COUNT,
    LOG_STATUS_W,
    PROJECT_P,
    PROJECT_STATUS_MARK,
    RULE,
    RULE_C,
    TICK,
    paint_projects_log,
    projects_log_entry_seats,
    projects_log_head_seats,
    projects_log_seats,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.sections.projects_log import ProjectsLogSection
from parch.spec import Spec


def test_projects_log_not_in_year_book():
    kinds = [page.kind for page in YearPlanner().pages(Spec(notes_pages=1))]
    assert kinds.count("projects") == 1
    assert "projects_log" not in kinds
    page = next(p for p in YearPlanner().pages(Spec(notes_pages=1)) if p.kind == "projects")
    assert any(isinstance(item, ProjectsBoard) for item in page.components)
    assert not any(isinstance(item, ProjectsLog) for item in page.components)


def test_projects_log_page():
    spec = Spec(notes_pages=1)
    page = ProjectsLogSection(spec).pages()[0]
    assert page.dest == "projects-log-2026"
    assert page.kind == "projects_log"
    assert page.title == "Projects"
    journal = next(item for item in page.components if isinstance(item, ProjectsLog))
    assert journal.year == 2026
    assert journal.entries == 6
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


def test_projects_log_seats_one_journal():
    well = well_rect(NOMAD)
    head, entries = projects_log_seats(well, 6)
    assert head.y == pytest.approx(well.y)
    assert head.h == pytest.approx(LOG_HEAD_H)
    assert head.x == pytest.approx(well.x)
    assert head.w == pytest.approx(well.w)
    assert len(entries) == 6
    assert entries[0].y == pytest.approx(head.bottom + LOG_BODY_GAP)
    assert entries[-1].bottom == pytest.approx(well.bottom)
    assert entries[1].y == pytest.approx(entries[0].bottom + LOG_ENTRY_GAP)
    for entry in entries:
        assert entry.x == pytest.approx(well.x)
        assert entry.w == pytest.approx(well.w)
        assert entry.h == pytest.approx(entries[0].h)

    name, status = projects_log_head_seats(head)
    assert name.x == pytest.approx(head.x)
    assert status.right == pytest.approx(head.right)
    assert name.right < status.x
    assert status.w == pytest.approx(LOG_STATUS_W)

    date, lines = projects_log_entry_seats(entries[0])
    assert date.x == pytest.approx(entries[0].x)
    assert date.w == pytest.approx(LOG_DATE_W)
    assert date.y == pytest.approx(entries[0].y)
    assert lines.x == pytest.approx(entries[0].x)
    assert lines.w == pytest.approx(entries[0].w)
    assert lines.y > date.bottom
    assert lines.bottom == pytest.approx(entries[0].bottom)


def test_projects_log_paint_dates_lines_and_status():
    journal = ProjectsLog(year=2026, entries=6)
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_projects_log(plotter, well, journal)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("P") == 1
    assert texts.count("Todo") == 1
    assert texts.count("Doing") == 1
    assert texts.count("Done") == 1
    for rejected in ("PROJECT", "Focus", "Notes", "TO DO", "IN PROGRESS", "DONE!", "Week"):
        assert rejected not in texts

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
    assert len(marks) == 3

    p_boxes = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(PROJECT_P)
    ]
    assert len(p_boxes) == 1

    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []

    date_rules = [
        op
        for op in plotter.ops
        if op[0] == "line"
        and op[5] == pytest.approx(RULE)
        and op[6] == pytest.approx(RULE_C)
        and op[3] - op[1] == pytest.approx(LOG_DATE_W)
    ]
    assert len(date_rules) == 6

    moved_rules = [
        op
        for op in plotter.ops
        if op[0] == "line"
        and op[5] == pytest.approx(RULE)
        and op[6] == pytest.approx(RULE_C)
        and op[3] - op[1] == pytest.approx(well.w)
    ]
    assert len(moved_rules) == 6 * LOG_LINE_COUNT

    seps = [
        op
        for op in plotter.ops
        if op[0] == "line" and op[5] == pytest.approx(HAIR) and op[3] - op[1] == pytest.approx(well.w)
    ]
    assert seps == []

    card_outlines = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(well.w)
    ]
    assert card_outlines == []


def test_projects_log_knobs():
    spec = Spec(notes_pages=1, project_log_entries=5)
    page = ProjectsLogSection(spec).pages()[0]
    journal = next(item for item in page.components if isinstance(item, ProjectsLog))
    assert journal.entries == 5
    well = well_rect(NOMAD)
    _, entries = projects_log_seats(well, journal.entries)
    assert len(entries) == 5
    plotter = RecordingPlotter()
    paint_projects_log(plotter, well, journal)
    date_rules = [
        op
        for op in plotter.ops
        if op[0] == "line"
        and op[5] == pytest.approx(RULE)
        and op[6] == pytest.approx(RULE_C)
        and op[3] - op[1] == pytest.approx(LOG_DATE_W)
    ]
    assert len(date_rules) == 5
    assert [op[2] for op in plotter.ops if op[0] == "text"].count("P") == 1


def test_projects_log_header_year_and_seven_tabs():
    spec = Spec(notes_pages=1)
    page = ProjectsLogSection(spec).pages()[0]
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Projects" in texts
    assert "2026" in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Week", "Day", "Notes"):
        assert label in texts
