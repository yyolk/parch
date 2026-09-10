import pytest

from parch.books import YearPlanner
from parch.components import MeetingAgenda, ProjectsBoard
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    MEET_COL_GAP,
    MEET_GAP,
    MEET_LABEL_W,
    TICK,
    checklist_content_height,
    meeting_attendees_height,
    meeting_head_height,
    meeting_head_seats,
    meeting_seats,
    paint_meeting,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.sections.meeting import MEET_ACTIONS, MEET_AGENDA, MEET_ATTENDEES, MeetingSection
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
    assert agenda.attendees == 3
    assert agenda.agenda == 5
    assert agenda.actions == 3
    assert MEET_ATTENDEES == 3
    assert MEET_AGENDA == 5
    assert MEET_ACTIONS == 3
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
    head, attendees, agenda, notes, actions = meeting_seats(well, 3, 5, 3)
    assert head.y == pytest.approx(well.y)
    assert head.h == pytest.approx(meeting_head_height())
    assert head.x == pytest.approx(well.x)
    assert attendees.y == pytest.approx(head.bottom + MEET_GAP)
    assert attendees.h == pytest.approx(meeting_attendees_height(3))
    assert attendees.w == pytest.approx(well.w)
    assert agenda.y == pytest.approx(attendees.bottom + MEET_GAP)
    assert agenda.h == pytest.approx(checklist_content_height(5))
    assert actions.y == pytest.approx(agenda.y)
    assert actions.h == pytest.approx(checklist_content_height(3))
    assert actions.x == pytest.approx(agenda.right + MEET_COL_GAP)
    assert agenda.w == pytest.approx(actions.w)
    assert notes.y > agenda.bottom
    assert notes.y == pytest.approx(agenda.bottom + MEET_GAP)
    assert notes.bottom == pytest.approx(well.bottom)
    assert notes.w == pytest.approx(well.w)
    assert notes.h > agenda.h
    assert notes.h > well.h * 0.35

    title, dated = meeting_head_seats(head)
    assert title.y > head.y
    assert dated.y > title.bottom
    assert title.h > dated.h
    assert title.w == pytest.approx(dated.w)
    assert MEET_LABEL_W < title.w / 4


def test_meeting_paint_template():
    agenda = MeetingAgenda(year=2026, attendees=3, agenda=5, actions=3)
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_meeting(plotter, well, agenda)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("Title") == 1
    assert texts.count("Date") == 1
    assert texts.count("Attendees") == 1
    assert texts.count("Agenda") == 1
    assert texts.count("Actions") == 1
    assert texts.count("Notes") == 1
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
    assert len(ticks) == 5 + 3

    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []


def test_meeting_knobs():
    agenda = MeetingAgenda(year=2026, attendees=2, agenda=4, actions=2)
    plotter = RecordingPlotter()
    paint_meeting(plotter, Rect(4, 20, 110, 90), agenda)
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 4 + 2
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Agenda" in texts
    assert "Actions" in texts


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
    for label in ("Year", "Quar", "Mon", "Habit", "Week", "Day", "Notes"):
        assert label in texts
    assert texts.count("Notes") == 2
