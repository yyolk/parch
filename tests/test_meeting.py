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
    MEET_INDEX_COL_GAP,
    MEET_INDEX_DATE_LABEL_W,
    MEET_INDEX_GAP,
    MEET_INDEX_MARK,
    MEET_INDEX_STUB_GAP,
    MEET_INDEX_STUB_W,
    MEET_INDEX_WEIGHTS,
    MEET_LABEL_W,
    MEET_WRITE_LABEL_H,
    TICK,
    checklist_content_height,
    meeting_head_height,
    meeting_head_seats,
    meeting_index_link_hits,
    meeting_index_row_parts,
    meeting_index_row_seats,
    meeting_seats,
    meetings_index_roster,
    paint_meeting,
    paint_meetings_index,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.sections.meeting import MEET_ACTION_ITEMS, MEET_AGENDA, MeetingSection
from parch.spec import Spec


def _rects_overlap(a: Rect, b: Rect) -> bool:
    return a.x < b.right and b.x < a.right and a.y < b.bottom and b.y < a.bottom


_MEET_STRIP = (
    ("Year", "year-2026"),
    ("Quar", "quarter-2026-Q1"),
    ("Mon", "month-2026-01"),
    ("Habit", "month-2026-01-habits"),
    ("Proj", "projects-index-2026-01"),
    ("Meet", "meetings-index-2026"),
    ("Task", "tasks-index-2026-Q1"),
    ("Rev", "review-index-2026"),
    ("Week", "week-2026-W01"),
    ("Day", "2026-01-01"),
    ("Notes", "2026-01-01-notes-1"),
)


def test_meeting_after_projects_in_year_book():
    spec = Spec(notes_pages=1)
    pages = YearPlanner().pages(spec)
    dests = [page.dest for page in pages]
    assert dests[2] == "projects-index-2026-01"
    assert dests[11] == "meetings-index-2026"
    assert dests[12:28] == [f"meeting-2026-{slot:02d}" for slot in range(1, 17)]
    assert dests[28] == "tasks-index-2026-Q1"
    assert dests[139] == "quarter-2026-Q1"
    assert [page.kind for page in pages].count("meetings_index") == 1
    assert [page.kind for page in pages].count("meeting") == 16


def test_meeting_index_page():
    spec = Spec(notes_pages=1)
    page = next(p for p in MeetingSection(spec).pages() if p.kind == "meetings_index")
    assert page.dest == "meetings-index-2026"
    assert page.title == "Meetings"
    roster = next(item for item in page.components if isinstance(item, MeetingIndex))
    assert roster.year == 2026
    assert roster.dest == "meetings-index-2026"
    assert len(roster.slots) == 16
    assert [slot.number for slot in roster.slots] == list(range(1, 17))
    assert [slot.dest for slot in roster.slots] == [
        f"meeting-2026-{slot:02d}" for slot in range(1, 17)
    ]
    assert strip_active(page.kind) == "Meet"
    assert strip_items(page) == _MEET_STRIP


def test_meeting_dest_page():
    spec = Spec(notes_pages=1)
    page = next(p for p in MeetingSection(spec).pages() if p.dest == "meeting-2026-03")
    assert page.kind == "meeting"
    assert page.title == "Meeting"
    agenda = next(item for item in page.components if isinstance(item, MeetingAgenda))
    assert agenda.year == 2026
    assert agenda.agenda == 4
    assert agenda.action_items == 3
    assert agenda.number == 3
    assert agenda.index_dest == "meetings-index-2026"
    assert not hasattr(agenda, "attendees")
    assert MEET_AGENDA == 4
    assert MEET_ACTION_ITEMS == 3
    assert strip_active(page.kind) == "Meet"
    assert strip_items(page) == _MEET_STRIP
    assert ("Meet", "meetings-index-2026") in strip_items(page)


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
    agenda = MeetingAgenda(year=2026, agenda=4, action_items=3, index_dest="meetings-index-2026", number=1)
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
    page = next(p for p in MeetingSection(spec).pages() if p.dest == "meeting-2026-01")
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Meeting" in texts
    assert "2026" in texts
    assert "01" in texts
    assert "Projects" not in texts
    assert "Attendees" not in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Proj", "Meet", "Task", "Rev", "Week", "Day", "Notes"):
        assert label in texts
    assert texts.count("Notes") == 2
    assert "Action items" in texts
    assert strip_active(page.kind) == "Meet"
    links = [op[2] for op in plotter.ops if op[0] == "link"]
    assert links.count("meetings-index-2026") >= 2


def test_meeting_index_seats():
    well = well_rect(NOMAD)
    seats = meetings_index_roster(well, 16)
    assert len(seats) == 16
    assert seats[0].y == pytest.approx(well.y)
    assert seats[0].x == pytest.approx(well.x)
    assert seats[0].w == pytest.approx(well.w)
    assert seats[-1].bottom == pytest.approx(well.bottom)
    assert seats[1].y > seats[0].bottom
    leftover = well.h - MEET_INDEX_GAP * 15
    assert seats[0].h == pytest.approx(leftover / 16)

    stub, body = meeting_index_row_parts(seats[0])
    assert stub.x > seats[0].x
    assert stub.w == pytest.approx(MEET_INDEX_STUB_W)
    assert body.x == pytest.approx(stub.right + MEET_INDEX_STUB_GAP)
    assert body.right < seats[0].right

    dated, title = meeting_index_row_seats(seats[0])
    assert dated.x == pytest.approx(body.x)
    assert title.right == pytest.approx(body.right)
    assert dated.x > stub.right
    assert dated.right < title.x
    assert title.x == pytest.approx(dated.right + MEET_INDEX_COL_GAP)
    share = dated.w + title.w
    assert dated.w / share == pytest.approx(MEET_INDEX_WEIGHTS[0] / sum(MEET_INDEX_WEIGHTS))
    assert title.w > dated.w
    assert dated.y == pytest.approx(title.y)
    assert dated.bottom == pytest.approx(title.bottom)
    hits = meeting_index_link_hits(seats[0])
    assert hits == (stub,)
    assert not _rects_overlap(hits[0], dated)
    assert not _rects_overlap(hits[0], title)


def test_meeting_index_paint_date_cues_and_links():
    spec = Spec(notes_pages=1)
    page = next(p for p in MeetingSection(spec).pages() if p.kind == "meetings_index")
    roster = next(item for item in page.components if isinstance(item, MeetingIndex))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_meetings_index(plotter, well, roster)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("Date") == 16
    for slot in range(1, 17):
        assert f"{slot:02d}" in texts
    assert "Title" not in texts
    assert "Attendees" not in texts
    assert "Agenda" not in texts
    assert "P" not in texts
    assert "Todo" not in texts
    assert "Atlas" not in texts

    date_boxes = [op[1] for op in plotter.ops if op[0] == "text" and op[2] == "Date"]
    assert len(date_boxes) == 16
    assert all(box.h == pytest.approx(MEET_WRITE_LABEL_H) for box in date_boxes)
    assert all(box.w == pytest.approx(MEET_INDEX_DATE_LABEL_W) for box in date_boxes)

    marks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(MEET_INDEX_MARK)
    ]
    assert len(marks) == 16

    seats = meetings_index_roster(well, 16)
    rules = [op for op in plotter.ops if op[0] == "line" and op[5] == pytest.approx(0.12)]
    assert len(rules) == 32
    for seat, date_box in zip(seats, date_boxes, strict=True):
        dated, title = meeting_index_row_seats(seat)
        assert date_box.bottom == pytest.approx(dated.bottom)
        assert date_box.bottom == pytest.approx(title.bottom)

    link_ops = [op for op in plotter.ops if op[0] == "link"]
    expected_hits: list[tuple[Rect, str]] = []
    for seat, slot in zip(seats, roster.slots, strict=True):
        hits = meeting_index_link_hits(seat)
        assert len(hits) == 1
        stub, body = meeting_index_row_parts(seat)
        dated, title = meeting_index_row_seats(seat)
        assert hits[0] == stub
        assert hits[0] != seat
        assert hits[0] != body
        assert not _rects_overlap(hits[0], dated)
        assert not _rects_overlap(hits[0], title)
        expected_hits.append((hits[0], slot.dest))
    assert [(op[1], op[2]) for op in link_ops] == expected_hits
    assert [dest for _, dest in expected_hits] == [
        f"meeting-2026-{slot:02d}" for slot in range(1, 17)
    ]
    for seat in seats:
        assert all(op[1] != seat for op in link_ops)
    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []

    chrome = RecordingPlotter()
    chrome.begin_page()
    PlannerLayout().paint(page, chrome, NOMAD)
    chrome_texts = [op[2] for op in chrome.ops if op[0] == "text"]
    assert "Meetings" in chrome_texts
    assert "Meet" in chrome_texts
    assert "2026" in chrome_texts
    assert strip_active(page.kind) == "Meet"
    assert dict(strip_items(page))["Meet"] == spec.meetings_index_dest


def test_meeting_rows_knob():
    spec = Spec(notes_pages=1, meeting_index_rows=12)
    pages = MeetingSection(spec).pages()
    index = next(p for p in pages if p.kind == "meetings_index")
    roster = next(item for item in index.components if isinstance(item, MeetingIndex))
    assert len(roster.slots) == 12
    dests = [page.dest for page in pages]
    assert dests[0] == "meetings-index-2026"
    assert dests[1:] == [f"meeting-2026-{slot:02d}" for slot in range(1, 13)]
    assert "meeting-2026-13" not in dests
    plotter = RecordingPlotter()
    paint_meetings_index(plotter, well_rect(NOMAD), roster)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("Date") == 12
    for slot in range(1, 13):
        assert f"{slot:02d}" in texts
    assert "13" not in texts
    assert [op[2] for op in plotter.ops if op[0] == "link"] == [
        f"meeting-2026-{slot:02d}" for slot in range(1, 13)
    ]
    well = well_rect(NOMAD)
    seats = meetings_index_roster(well, 12)
    link_boxes = [op[1] for op in plotter.ops if op[0] == "link"]
    assert link_boxes == [meeting_index_link_hits(seat)[0] for seat in seats]
