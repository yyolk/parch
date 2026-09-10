import pytest

from parch.books import YearPlanner
from parch.components import MeetingAgenda, ProjectsBoard
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    MEET_GAP,
    MEET_HEAD_COL_GAP,
    MEET_LABEL_W,
    MEET_WRITE_LABEL_H,
    TICK,
    checklist_content_height,
    meeting_head_height,
    meeting_head_seats,
    meeting_seats,
    paint_meeting,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.sections.meeting import MEET_ACTION_ITEMS, MEET_AGENDA, MeetingSection
from parch.spec import Spec


def test_meeting_not_in_year_book():
    kinds = [page.kind for page in YearPlanner().pages(Spec(notes_pages=1))]
    assert kinds.count("projects") == 1
    assert "meeting" not in kinds
    assert "projects_meeting" not in kinds
    page = next(p for p in YearPlanner().pages(Spec(notes_pages=1)) if p.kind == "projects")
    assert any(isinstance(item, ProjectsBoard) for item in page.components)
    assert not any(isinstance(item, MeetingAgenda) for item in page.components)


def test_meeting_page():
    spec = Spec(notes_pages=1)
    page = MeetingSection(spec).pages()[0]
    assert page.dest == "meeting-2026"
    assert page.kind == "meeting"
    assert page.title == "Meeting"
    agenda = next(item for item in page.components if isinstance(item, MeetingAgenda))
    assert agenda.year == 2026
    assert agenda.agenda == 4
    assert agenda.action_items == 3
    assert not hasattr(agenda, "attendees")
    assert MEET_AGENDA == 4
    assert MEET_ACTION_ITEMS == 3
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


def test_meeting_seats_stack():
    well = well_rect(NOMAD)
    head, agenda, notes, action_items = meeting_seats(well, 4, 3)
    assert head.y == pytest.approx(well.y)
    assert head.h == pytest.approx(meeting_head_height())
    assert head.x == pytest.approx(well.x)
    assert head.w == pytest.approx(well.w)
    assert agenda.y == pytest.approx(head.bottom + MEET_GAP)
    assert agenda.h == pytest.approx(checklist_content_height(4))
    assert agenda.w == pytest.approx(well.w)
    assert notes.y == pytest.approx(agenda.bottom + MEET_GAP)
    assert notes.w == pytest.approx(well.w)
    assert action_items.y == pytest.approx(notes.bottom + MEET_GAP)
    assert action_items.bottom == pytest.approx(well.bottom)
    assert action_items.h == pytest.approx(checklist_content_height(3))
    assert action_items.w == pytest.approx(well.w)
    assert notes.h > agenda.h
    assert notes.h > action_items.h
    assert notes.h > well.h * 0.4

    title, dated = meeting_head_seats(head)
    assert title.y == pytest.approx(dated.y)
    assert title.h == pytest.approx(dated.h)
    assert title.bottom == pytest.approx(dated.bottom)
    assert dated.x == pytest.approx(title.right + MEET_HEAD_COL_GAP)
    assert title.w > dated.w
    assert MEET_LABEL_W < title.w / 3


def test_meeting_paint_template():
    agenda = MeetingAgenda(year=2026, agenda=4, action_items=3)
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_meeting(plotter, well, agenda)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("Title") == 1
    assert texts.count("Date") == 1
    assert texts.count("Agenda") == 1
    assert texts.count("Action items") == 1
    assert texts.count("Notes") == 1
    assert "Attendees" not in texts
    assert "Actions" not in texts
    assert "P" not in texts
    assert "Todo" not in texts
    assert "Doing" not in texts
    assert "Done" not in texts
    assert "Projects" not in texts
    for rejected in ("PROJECT", "Focus", "This week", "This month", "Someday"):
        assert rejected not in texts

    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 4 + 3

    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []

    title_box = next(op[1] for op in plotter.ops if op[0] == "text" and op[2] == "Title")
    date_box = next(op[1] for op in plotter.ops if op[0] == "text" and op[2] == "Date")
    assert title_box.h == pytest.approx(MEET_WRITE_LABEL_H)
    assert date_box.h == pytest.approx(MEET_WRITE_LABEL_H)
    rules = [
        op
        for op in plotter.ops
        if op[0] == "line" and op[2] == pytest.approx(title_box.bottom)
    ]
    assert len(rules) >= 2
    assert title_box.bottom == pytest.approx(date_box.bottom)


def test_meeting_knobs():
    agenda = MeetingAgenda(year=2026, agenda=3, action_items=2)
    plotter = RecordingPlotter()
    paint_meeting(plotter, Rect(4, 20, 110, 90), agenda)
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 3 + 2
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Agenda" in texts
    assert "Action items" in texts
    assert "Attendees" not in texts


def test_meeting_header_year_and_seven_tabs():
    spec = Spec(notes_pages=1)
    page = MeetingSection(spec).pages()[0]
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Meeting" in texts
    assert "2026" in texts
    assert "Projects" not in texts
    assert "Attendees" not in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Week", "Day", "Notes"):
        assert label in texts
    assert texts.count("Notes") == 2
    assert "Action items" in texts
    assert "Meet" not in (label for label, _ in strip_items(page))
