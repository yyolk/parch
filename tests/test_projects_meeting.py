import pytest

from parch.books import YearPlanner
from parch.components import ProjectsBoard, ProjectsMeeting
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    MEETING_GAP,
    MEETING_LABEL_W,
    MEETING_NAME_H,
    MEETING_ROW_GAP,
    MEETING_ROW_INSET_X,
    MEETING_TASK_COL_GAP,
    PROJECT_P,
    PROJECT_STATUS_MARK,
    TICK,
    meeting_head_height,
    meeting_roster_height,
    meeting_row_height,
    paint_projects_meeting,
    projects_meeting_head_seats,
    projects_meeting_row_seats,
    projects_meeting_rows,
    projects_meeting_seats,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.sections.projects_meeting import MEETING_CARDS, MEETING_TASKS, ProjectsMeetingSection
from parch.spec import Spec


def test_projects_meeting_not_in_year_book():
    kinds = [page.kind for page in YearPlanner().pages(Spec(notes_pages=1))]
    assert kinds.count("projects") == 1
    assert "projects_meeting" not in kinds
    page = next(p for p in YearPlanner().pages(Spec(notes_pages=1)) if p.kind == "projects")
    assert any(isinstance(item, ProjectsBoard) for item in page.components)
    assert not any(isinstance(item, ProjectsMeeting) for item in page.components)


def test_projects_meeting_page():
    spec = Spec(notes_pages=1)
    page = ProjectsMeetingSection(spec).pages()[0]
    assert page.dest == "projects-meeting-2026"
    assert page.kind == "projects_meeting"
    assert page.title == "Projects"
    board = next(item for item in page.components if isinstance(item, ProjectsMeeting))
    assert board.year == 2026
    assert board.cards == 3
    assert board.tasks == 3
    assert MEETING_CARDS == 3
    assert MEETING_TASKS == 3
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


def test_projects_meeting_seats_sandwich():
    well = well_rect(NOMAD)
    head, roster, notes = projects_meeting_seats(well, 3)
    assert head.y == pytest.approx(well.y)
    assert head.h == pytest.approx(meeting_head_height())
    assert head.x == pytest.approx(well.x)
    assert notes.bottom == pytest.approx(well.bottom)
    assert notes.right == pytest.approx(well.right)
    assert roster.y == pytest.approx(head.bottom + MEETING_GAP)
    assert notes.y == pytest.approx(roster.bottom + MEETING_GAP)
    assert roster.h == pytest.approx(meeting_roster_height(3))
    assert notes.h > roster.h
    assert notes.h > head.h
    assert notes.h > well.h * 0.45

    slots = projects_meeting_rows(roster, 3)
    assert len(slots) == 3
    assert slots[0].x == pytest.approx(roster.x)
    assert slots[0].w == pytest.approx(roster.w)
    assert slots[-1].bottom == pytest.approx(roster.bottom)
    assert slots[1].y == pytest.approx(slots[0].bottom + MEETING_ROW_GAP)
    assert slots[0].h == pytest.approx(meeting_row_height())
    assert slots[0].h < well.h / 6

    name, tasks = projects_meeting_row_seats(slots[0])
    assert name.y > slots[0].y
    assert name.h == pytest.approx(MEETING_NAME_H)
    assert tasks.y > name.bottom
    assert tasks.h == pytest.approx(TICK)
    assert tasks.w > name.w * 0.9

    meeting, dated = projects_meeting_head_seats(head)
    assert meeting.y > head.y
    assert dated.y > meeting.bottom
    assert dated.bottom < head.bottom
    assert meeting.w == pytest.approx(dated.w)
    assert meeting.h > dated.h
    assert meeting.x == pytest.approx(head.x + 1.8)
    assert MEETING_LABEL_W < meeting.w / 3


def test_projects_meeting_paint_rows_ticks_and_decisions():
    board = ProjectsMeeting(year=2026, cards=3, tasks=3)
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_projects_meeting(plotter, well, board)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("P") == 3
    assert texts.count("Meeting") == 1
    assert texts.count("Date") == 1
    assert texts.count("Decisions") == 1
    assert texts.count("Todo") == 0
    assert texts.count("Doing") == 0
    assert texts.count("Done") == 0
    assert "Notes" not in texts
    assert "Week" not in texts
    for rejected in (
        "PROJECT",
        "Focus",
        "TO DO",
        "IN PROGRESS",
        "DONE!",
        "This week",
        "This month",
        "Someday",
    ):
        assert rejected not in texts

    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 3 * 3

    xs = sorted({round(op[1].x, 3) for op in ticks})
    assert len(xs) == 3
    assert xs[1] - xs[0] == pytest.approx(
        (well.w - 2 * MEETING_ROW_INSET_X - 2 * MEETING_TASK_COL_GAP) / 3 + MEETING_TASK_COL_GAP,
        abs=0.2,
    )

    p_boxes = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(PROJECT_P)
    ]
    assert len(p_boxes) == 3

    status = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[2]
        and not op[3]
        and op[1].w == pytest.approx(PROJECT_STATUS_MARK)
    ]
    assert status == []

    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []

    outlines = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(well.w)
    ]
    # meeting head + 3 capture rows + decisions well
    assert len(outlines) == 5


def test_projects_meeting_two_ticks():
    board = ProjectsMeeting(year=2026, cards=3, tasks=2)
    plotter = RecordingPlotter()
    paint_projects_meeting(plotter, Rect(4, 20, 110, 90), board)
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 3 * 2
    assert [op[2] for op in plotter.ops if op[0] == "text"].count("P") == 3


def test_projects_meeting_header_year_and_seven_tabs():
    spec = Spec(notes_pages=1)
    page = ProjectsMeetingSection(spec).pages()[0]
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Projects" in texts
    assert "2026" in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Week", "Day", "Notes"):
        assert label in texts
    assert "Meeting" in texts
    assert "Decisions" in texts
