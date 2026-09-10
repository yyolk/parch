import pytest

from parch.books import YearPlanner
from parch.components import MeetingAgenda, MeetingsIndex
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    MEET_GAP,
    MEET_HEAD_COL_GAP,
    MEET_LABEL_W,
    MEET_PREVIEW_TICK,
    MEET_TICKET_WRITE_PAD,
    MEET_WRITE_LABEL_H,
    TICK,
    TICKET_MARK,
    TICKET_STUB_W,
    checklist_content_height,
    meeting_head_height,
    meeting_head_seats,
    meeting_seats,
    meeting_ticket_body_seats,
    meeting_ticket_link_hits,
    meeting_ticket_parts,
    meeting_ticket_preview_bands,
    meeting_ticket_seats,
    meeting_ticket_write_in,
    paint_meeting,
    paint_meetings_index_tickets,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.sections.meeting import MEET_ACTION_ITEMS, MEET_AGENDA
from parch.spec import Spec


def _rects_overlap(a: Rect, b: Rect) -> bool:
    return a.x < b.right and b.x < a.right and a.y < b.bottom and b.y < a.bottom


_MEET_STRIP = (
    ("Year", "year-2026"),
    ("Quar", "quarter-2026-Q1"),
    ("Mon", "month-2026-01"),
    ("Habit", "month-2026-01-habits"),
    ("Proj", "projects-index-2026-01"),
    ("Meet", "meeting-index-2026-01"),
    ("Week", "week-2026-W01"),
    ("Day", "2026-01-01"),
    ("Notes", "2026-01-01-notes-1"),
)


def test_meeting_index_and_dests_in_year_book():
    spec = Spec(notes_pages=1)
    pages = YearPlanner().pages(spec)
    dests = [page.dest for page in pages]
    assert dests[2] == "projects-2026"
    assert dests[3] == "projects-index-2026-01"
    assert dests[12] == "meeting-index-2026-01"
    assert dests[13:21] == [f"meeting-2026-{slot:02d}" for slot in range(1, 9)]
    assert dests[21] == "quarter-2026-Q1"

    index = pages[12]
    assert index.kind == "meetings_index"
    assert index.title == "Meeting"
    assert strip_active(index.kind) == "Meet"
    assert strip_items(index) == _MEET_STRIP

    roster = next(item for item in index.components if isinstance(item, MeetingsIndex))
    assert roster.year == 2026
    assert roster.dest == "meeting-index-2026-01"
    assert len(roster.tickets) == 8
    assert [ticket.dest for ticket in roster.tickets] == [
        f"meeting-2026-{slot:02d}" for slot in range(1, 9)
    ]
    assert [ticket.number for ticket in roster.tickets] == list(range(1, 9))

    leaf = next(page for page in pages if page.dest == "meeting-2026-03")
    assert leaf.kind == "meeting"
    assert leaf.title == "Meeting"
    assert strip_active(leaf.kind) == "Meet"
    assert ("Meet", "meeting-index-2026-01") in strip_items(leaf)
    agenda = next(item for item in leaf.components if isinstance(item, MeetingAgenda))
    assert agenda.agenda == 4
    assert agenda.action_items == 3
    assert agenda.number == 3
    assert agenda.index_dest == "meeting-index-2026-01"
    assert not hasattr(agenda, "attendees")
    assert MEET_AGENDA == 4
    assert MEET_ACTION_ITEMS == 3


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


def test_meeting_ticket_seats():
    well = Rect(4, 20, 110, 90)
    seats = meeting_ticket_seats(well, 8)
    assert len(seats) == 8
    assert seats[0].y == pytest.approx(well.y)
    assert seats[-1].bottom == pytest.approx(well.bottom)
    stub, body = meeting_ticket_parts(seats[0])
    assert stub.w == pytest.approx(TICKET_STUB_W)
    name, preview = meeting_ticket_body_seats(body)
    write = meeting_ticket_write_in(name)
    assert write.x == pytest.approx(name.x)
    assert write.right == pytest.approx(name.right)
    assert write.right < preview.x
    assert write.h == pytest.approx(max(name.h - MEET_TICKET_WRITE_PAD, 1))
    head, agenda, notes, actions = meeting_ticket_preview_bands(preview)
    assert head.y > preview.y
    assert actions.bottom < preview.bottom
    assert agenda.y > head.bottom
    assert notes.y > agenda.bottom
    assert actions.y > notes.bottom
    assert notes.h > agenda.h


def test_meetings_index_paint_write_in_and_links():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "meetings_index")
    roster = next(item for item in page.components if isinstance(item, MeetingsIndex))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_meetings_index_tickets(plotter, well, roster)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    for slot in range(1, 9):
        assert f"{slot:02d}" in texts
    assert "P" not in texts
    assert "Todo" not in texts
    assert "Attendees" not in texts
    assert "Agenda" not in texts

    stubs = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICKET_MARK)
    ]
    assert len(stubs) == 8

    preview_ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[2]
        and not op[3]
        and op[1].w == pytest.approx(MEET_PREVIEW_TICK)
    ]
    assert len(preview_ticks) == 8 * (4 + 3)

    seats = meeting_ticket_seats(well, 8)
    rules = [
        op
        for op in plotter.ops
        if op[0] == "line" and op[5] == pytest.approx(0.12)
    ]
    write_rules = []
    for seat in seats:
        _, body = meeting_ticket_parts(seat)
        name, preview = meeting_ticket_body_seats(body)
        write = meeting_ticket_write_in(name)
        match = [
            op
            for op in rules
            if op[1] == pytest.approx(write.x)
            and op[2] == pytest.approx(write.bottom)
            and op[3] == pytest.approx(write.right)
        ]
        assert match
        write_rules.extend(match)
        assert write.right < preview.x
    assert len(write_rules) == 8

    link_ops = [op for op in plotter.ops if op[0] == "link"]
    expected_hits: list[tuple[Rect, str]] = []
    for seat, ticket in zip(seats, roster.tickets, strict=True):
        hits = meeting_ticket_link_hits(seat)
        assert len(hits) == 2
        stub, body = meeting_ticket_parts(seat)
        name, preview = meeting_ticket_body_seats(body)
        write = meeting_ticket_write_in(name)
        assert hits[0] == stub
        assert hits[1] == preview
        for hit in hits:
            assert not _rects_overlap(hit, write)
        expected_hits.extend((hit, ticket.dest) for hit in hits)
    assert [(op[1], op[2]) for op in link_ops] == expected_hits
    assert [dest for _, dest in expected_hits] == [
        dest for slot in range(1, 9) for dest in (f"meeting-2026-{slot:02d}",) * 2
    ]
    for seat in seats:
        assert all(op[1] != seat for op in link_ops)
    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []

    chrome = RecordingPlotter()
    chrome.begin_page()
    PlannerLayout().paint(page, chrome, NOMAD)
    chrome_texts = [op[2] for op in chrome.ops if op[0] == "text"]
    assert "Meeting" in chrome_texts
    assert "Meet" in chrome_texts
    assert "2026" in chrome_texts


def test_meeting_dest_chip_and_lit_meet():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.dest == "meeting-2026-01")
    agenda = next(item for item in page.components if isinstance(item, MeetingAgenda))
    assert agenda.number == 1
    chrome = RecordingPlotter()
    chrome.begin_page()
    PlannerLayout().paint(page, chrome, NOMAD)
    labels = [op[2] for op in chrome.ops if op[0] == "text"]
    assert "Meeting" in labels
    assert "01" in labels
    assert "Index" not in labels
    assert "Meet" in labels
    assert "Attendees" not in labels
    assert "Title" in labels
    assert "Action items" in labels
    assert strip_active(page.kind) == "Meet"
    assert dict(strip_items(page))["Meet"] == spec.meetings_index_dest
    assert spec.meetings_index_dest == "meeting-index-2026-01"
    leaf_links = [op[2] for op in chrome.ops if op[0] == "link"]
    chip_links = [dest for dest in leaf_links if dest == spec.meetings_index_dest]
    assert len(chip_links) >= 2
    assert spec.projects_dest not in leaf_links


def test_meeting_tickets_knob():
    spec = Spec(notes_pages=1, meeting_tickets=6)
    pages = YearPlanner().pages(spec)
    roster = next(
        item
        for page in pages
        if page.kind == "meetings_index"
        for item in page.components
        if isinstance(item, MeetingsIndex)
    )
    assert len(roster.tickets) == 6
    dests = [page.dest for page in pages]
    assert "meeting-2026-06" in dests
    assert "meeting-2026-07" not in dests
    plotter = RecordingPlotter()
    paint_meetings_index_tickets(plotter, Rect(4, 20, 110, 90), roster)
    assert [op[2] for op in plotter.ops if op[0] == "link"] == [
        dest for slot in range(1, 7) for dest in (f"meeting-2026-{slot:02d}",) * 2
    ]


def test_meeting_index_pages_knob():
    spec = Spec(notes_pages=1, meeting_index_pages=3)
    assert spec.meeting_count == 24
    pages = YearPlanner().pages(spec)
    dests = [page.dest for page in pages]
    assert dests[12:15] == [
        "meeting-index-2026-01",
        "meeting-index-2026-02",
        "meeting-index-2026-03",
    ]
    assert dests[15:39] == [f"meeting-2026-{slot:02d}" for slot in range(1, 25)]
    assert dests[39] == "quarter-2026-Q1"

    indexes = [page for page in pages if page.kind == "meetings_index"]
    assert len(indexes) == 3
    slices = [
        [
            ticket.number
            for ticket in next(
                item for item in page.components if isinstance(item, MeetingsIndex)
            ).tickets
        ]
        for page in indexes
    ]
    assert slices == [list(range(1, 9)), list(range(9, 17)), list(range(17, 25))]

    page_two = next(item for item in indexes[1].components if isinstance(item, MeetingsIndex))
    plotter = RecordingPlotter()
    paint_meetings_index_tickets(plotter, well_rect(NOMAD), page_two)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "09" in texts
    assert "16" in texts
    assert "01" not in texts
    assert [op[2] for op in plotter.ops if op[0] == "link"] == [
        dest for slot in range(9, 17) for dest in (f"meeting-2026-{slot:02d}",) * 2
    ]

    leaf = next(page for page in pages if page.dest == "meeting-2026-10")
    agenda = next(item for item in leaf.components if isinstance(item, MeetingAgenda))
    assert agenda.number == 10
    assert agenda.index_dest == "meeting-index-2026-02"
    assert dict(strip_items(leaf))["Meet"] == "meeting-index-2026-02"
    chrome = RecordingPlotter()
    chrome.begin_page()
    PlannerLayout().paint(leaf, chrome, NOMAD)
    labels = [op[2] for op in chrome.ops if op[0] == "text"]
    assert "10" in labels
    assert "Index" not in labels
    assert "meeting-index-2026-02" in [op[2] for op in chrome.ops if op[0] == "link"]
    assert "meeting-index-2026-01" not in [op[2] for op in chrome.ops if op[0] == "link"]

    year = next(page for page in pages if page.kind == "annual")
    assert dict(strip_items(year))["Meet"] == spec.meetings_index_dest
    assert spec.meetings_index_dest == "meeting-index-2026-01"
