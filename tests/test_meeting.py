import pytest

from parch.books import YearPlanner
from parch.components import MeetingAgenda, MeetingIndex
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    MEET_GAP,
    MEET_HEAD_COL_GAP,
    MEET_INDEX_FOCUS_AGENDA,
    MEET_INDEX_FOCUS_GAP,
    MEET_INDEX_FOCUS_WEIGHTS,
    MEET_INDEX_LIST_MARK,
    MEET_INDEX_MARK,
    MEET_LABEL_W,
    MEET_WRITE_LABEL_H,
    TICK,
    checklist_content_height,
    meeting_head_height,
    meeting_head_seats,
    meeting_seats,
    meetings_index_focus_parts,
    meetings_index_focus_seats,
    meetings_index_list_row,
    paint_meeting,
    paint_meetings_index_focus,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.sections.meeting import MEET_ACTION_ITEMS, MEET_AGENDA, MeetingSection
from parch.spec import Spec

_MEET_STRIP = (
    ("Year", "year-2026"),
    ("Quar", "quarter-2026-Q1"),
    ("Mon", "month-2026-01"),
    ("Habit", "month-2026-01-habits"),
    ("Proj", "projects-index-2026-01"),
    ("Meet", "meetings-index-2026"),
    ("Week", "week-2026-W01"),
    ("Day", "2026-01-01"),
    ("Notes", "2026-01-01-notes-1"),
)


def test_meetings_after_projects_and_meet_nav():
    spec = Spec(notes_pages=1)
    pages = YearPlanner().pages(spec)
    dests = [page.dest for page in pages]
    assert dests[2] == "projects-2026"
    assert dests[3] == "projects-index-2026-01"
    assert dests[4:12] == [f"projects-2026-{slot:02d}" for slot in range(1, 9)]
    assert dests[12] == "meetings-index-2026"
    assert dests[13:21] == [f"meeting-2026-{slot:02d}" for slot in range(1, 9)]
    assert dests[21] == "quarter-2026-Q1"

    index = pages[12]
    assert index.kind == "meetings_index"
    assert index.title == "Meetings"
    assert strip_active(index.kind) == "Meet"
    assert strip_items(index) == _MEET_STRIP

    roster = next(item for item in index.components if isinstance(item, MeetingIndex))
    assert roster.year == 2026
    assert roster.dest == "meetings-index-2026"
    assert roster.featured.number == 1
    assert roster.featured.dest == "meeting-2026-01"
    assert [slot.dest for slot in roster.entries] == [
        f"meeting-2026-{slot:02d}" for slot in range(2, 9)
    ]
    assert [slot.number for slot in roster.entries] == list(range(2, 9))

    leaf = next(page for page in pages if page.dest == "meeting-2026-03")
    assert leaf.kind == "meeting"
    assert leaf.title == "Meeting"
    assert strip_active(leaf.kind) == "Meet"
    assert strip_items(leaf) == _MEET_STRIP
    agenda = next(item for item in leaf.components if isinstance(item, MeetingAgenda))
    assert agenda.year == 2026
    assert agenda.agenda == 4
    assert agenda.action_items == 3
    assert agenda.number == 3
    assert agenda.dest == "meeting-2026-03"
    assert agenda.index_dest == "meetings-index-2026"
    assert not hasattr(agenda, "attendees")
    assert MEET_AGENDA == 4
    assert MEET_ACTION_ITEMS == 3


def test_meeting_section_builds_index_and_dests():
    spec = Spec(notes_pages=1)
    pages = MeetingSection(spec).pages()
    assert pages[0].dest == "meetings-index-2026"
    assert [page.dest for page in pages[1:]] == [
        f"meeting-2026-{slot:02d}" for slot in range(1, 9)
    ]
    assert all(page.kind == "meeting" for page in pages[1:])


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
    agenda = MeetingAgenda(year=2026, agenda=4, action_items=3, number=1)
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


def test_meeting_header_year_chip_and_meet_tab():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.dest == "meeting-2026-01")
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Meeting" in texts
    assert "2026" in texts
    assert "01" in texts
    assert "Projects" not in texts
    assert "Attendees" not in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Proj", "Meet", "Week", "Day", "Notes"):
        assert label in texts
    assert texts.count("Notes") == 2
    assert "Action items" in texts
    chip_links = [op[2] for op in plotter.ops if op[0] == "link" and op[2] == "meetings-index-2026"]
    assert chip_links
    assert dict(strip_items(page))["Meet"] == spec.meetings_index_dest


def test_meetings_index_focus_seats():
    well = Rect(4, 20, 110, 90)
    focus, listing = meetings_index_focus_seats(well, 7)
    assert focus.x == pytest.approx(well.x)
    assert focus.y == pytest.approx(well.y)
    assert focus.w == pytest.approx(well.w)
    assert listing[0].y > focus.bottom
    assert listing[-1].bottom == pytest.approx(well.bottom)
    assert len(listing) == 7
    leftover = well.h - MEET_INDEX_FOCUS_GAP
    assert focus.h == pytest.approx(
        leftover * MEET_INDEX_FOCUS_WEIGHTS[0] / sum(MEET_INDEX_FOCUS_WEIGHTS)
    )
    band_h = leftover * MEET_INDEX_FOCUS_WEIGHTS[1] / sum(MEET_INDEX_FOCUS_WEIGHTS)
    assert listing[-1].bottom - listing[0].y == pytest.approx(band_h)
    assert focus.h > listing[0].h

    stub, head, agenda = meetings_index_focus_parts(focus)
    assert stub.x > focus.x
    assert head.x == pytest.approx(stub.right)
    assert agenda.y > head.bottom
    assert agenda.bottom < focus.bottom
    assert head.w > stub.w

    row_stub, row_title, row_date = meetings_index_list_row(listing[0])
    assert row_stub.x > listing[0].x
    assert row_title.x == pytest.approx(row_stub.right)
    assert row_date.x == pytest.approx(row_title.right + MEET_HEAD_COL_GAP)
    assert row_date.right < listing[0].right
    assert row_title.w > row_date.w


def test_meetings_index_focus_paint_links():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "meetings_index")
    roster = next(item for item in page.components if isinstance(item, MeetingIndex))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_meetings_index_focus(plotter, well, roster)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("Title") == 1
    assert texts.count("Date") == 1
    assert texts.count("Agenda") == 1
    assert "Action items" not in texts
    assert "Attendees" not in texts
    assert "P" not in texts
    assert "Todo" not in texts
    assert "Projects" not in texts
    for slot in range(1, 9):
        assert f"{slot:02d}" in texts

    hero_marks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(MEET_INDEX_MARK)
    ]
    assert len(hero_marks) == 1
    hero = hero_marks[0][1]
    title_box = next(op[1] for op in plotter.ops if op[0] == "text" and op[2] == "Title")
    assert hero.y < title_box.bottom
    assert hero.bottom > title_box.y
    list_marks = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[2]
        and not op[3]
        and op[1].w == pytest.approx(MEET_INDEX_LIST_MARK)
    ]
    assert len(list_marks) == 7

    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == MEET_INDEX_FOCUS_AGENDA

    links = [op[2] for op in plotter.ops if op[0] == "link"]
    assert links[0] == "meeting-2026-01"
    assert links[1:] == [f"meeting-2026-{slot:02d}" for slot in range(2, 9)]
    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []


def test_meetings_index_header_and_meet_active():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "meetings_index")
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Meetings" in texts
    assert "2026" in texts
    assert "Meet" in texts
    assert "Action items" not in texts
    links = [op[2] for op in plotter.ops if op[0] == "link"]
    assert "meeting-2026-01" in links
    assert "meeting-2026-08" in links
    assert spec.meetings_index_dest in links


def test_meeting_index_rows_knob():
    spec = Spec(notes_pages=1, meeting_index_rows=6)
    pages = YearPlanner().pages(spec)
    roster = next(
        item
        for page in pages
        if page.kind == "meetings_index"
        for item in page.components
        if isinstance(item, MeetingIndex)
    )
    assert len(roster.entries) == 6
    dests = [page.dest for page in pages]
    assert "meeting-2026-07" in dests
    assert "meeting-2026-08" not in dests
    plotter = RecordingPlotter()
    paint_meetings_index_focus(plotter, Rect(4, 20, 110, 90), roster)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "07" in texts
    assert "08" not in texts
    links = [op[2] for op in plotter.ops if op[0] == "link"]
    assert links[0] == "meeting-2026-01"
    assert len(links) == 7
