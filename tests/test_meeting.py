import math

import pytest

from parch.books import YearPlanner
from parch.components import MeetingAgenda, MeetingsIndex
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    COVER_COLS,
    COVER_DATE_WEIGHTS,
    COVER_GAP,
    COVER_HEAD_H,
    COVER_INSET_X,
    COVER_INSET_Y,
    MEET_GAP,
    MEET_HEAD_COL_GAP,
    MEET_LABEL_W,
    MEET_WRITE_LABEL_H,
    TICK,
    checklist_content_height,
    meeting_cover_head,
    meeting_cover_head_seats,
    meeting_head_height,
    meeting_head_seats,
    meeting_index_covers,
    meeting_seats,
    paint_meeting,
    paint_meetings_index_covers,
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
    ("Meet", "meetings-index-2026-01"),
    ("Week", "week-2026-W01"),
    ("Day", "2026-01-01"),
    ("Notes", "2026-01-01-notes-1"),
)


def test_meetings_after_projects_in_year_book():
    spec = Spec(notes_pages=1)
    pages = YearPlanner().pages(spec)
    dests = [page.dest for page in pages]
    assert dests[2] == "projects-2026"
    assert dests[3] == "projects-index-2026-01"
    assert dests[4:12] == [f"projects-2026-{slot:02d}" for slot in range(1, 9)]
    assert dests[12] == "meetings-index-2026-01"
    assert dests[13:19] == [f"meeting-2026-{slot:02d}" for slot in range(1, 7)]
    assert dests[19] == "quarter-2026-Q1"

    index = pages[12]
    assert index.kind == "meetings_index"
    assert index.title == "Meetings"
    assert strip_active(index.kind) == "Meet"
    assert strip_items(index) == _MEET_STRIP

    roster = next(item for item in index.components if isinstance(item, MeetingsIndex))
    assert roster.year == 2026
    assert roster.dest == "meetings-index-2026-01"
    assert len(roster.covers) == 6
    assert [cover.dest for cover in roster.covers] == [
        f"meeting-2026-{slot:02d}" for slot in range(1, 7)
    ]
    assert [cover.number for cover in roster.covers] == list(range(1, 7))

    leaf = next(page for page in pages if page.dest == "meeting-2026-03")
    assert leaf.kind == "meeting"
    assert leaf.title == "Meeting"
    assert strip_active(leaf.kind) == "Meet"
    assert ("Meet", "meetings-index-2026-01") in strip_items(leaf)
    agenda = next(item for item in leaf.components if isinstance(item, MeetingAgenda))
    assert agenda.agenda == 4
    assert agenda.action_items == 3
    assert agenda.number == 3
    assert agenda.index_dest == "meetings-index-2026-01"
    assert not hasattr(agenda, "attendees")


def test_meeting_dest_is_locked_template():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.dest == "meeting-2026-01")
    agenda = next(item for item in page.components if isinstance(item, MeetingAgenda))
    assert agenda.agenda == MEET_AGENDA == 4
    assert agenda.action_items == MEET_ACTION_ITEMS == 3
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
    assert "Projects" not in texts
    for rejected in ("Focus", "This week", "This month", "Someday"):
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
    assert dated.x == pytest.approx(title.right + MEET_HEAD_COL_GAP)
    assert title.w > dated.w
    assert MEET_LABEL_W < title.w / 3


def test_meeting_cover_grid_seats():
    well = well_rect(NOMAD)
    seats = meeting_index_covers(well, 6)
    assert len(seats) == 6
    assert COVER_COLS == 2
    assert seats[0].x == pytest.approx(well.x)
    assert seats[0].y == pytest.approx(well.y)
    assert seats[1].x > seats[0].right
    assert seats[1].y == pytest.approx(seats[0].y)
    assert seats[2].y > seats[0].bottom
    assert seats[2].x == pytest.approx(seats[0].x)
    assert seats[5].bottom == pytest.approx(well.bottom)
    assert seats[1].right == pytest.approx(well.right)
    leftover_w = well.w - COVER_GAP
    assert seats[0].w == pytest.approx(leftover_w / 2)
    leftover_h = well.h - COVER_GAP * 2
    assert seats[0].h == pytest.approx(leftover_h / 3)
    assert seats[1].x - seats[0].right == pytest.approx(COVER_GAP)
    assert seats[2].y - seats[0].bottom == pytest.approx(COVER_GAP)

    head = meeting_cover_head(seats[0])
    assert head.x == pytest.approx(seats[0].x + COVER_INSET_X)
    assert head.y == pytest.approx(seats[0].y + COVER_INSET_Y)
    assert head.h == pytest.approx(COVER_HEAD_H)
    assert COVER_HEAD_H == pytest.approx(meeting_head_height())
    title, dated = meeting_cover_head_seats(head)
    assert title.y == pytest.approx(dated.y)
    assert dated.x == pytest.approx(title.right + MEET_HEAD_COL_GAP)
    share = title.w + dated.w
    assert title.w / share == pytest.approx(COVER_DATE_WEIGHTS[0] / sum(COVER_DATE_WEIGHTS))
    assert title.w > dated.w


def test_meetings_index_paint_covers_and_links():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "meetings_index")
    roster = next(item for item in page.components if isinstance(item, MeetingsIndex))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_meetings_index_covers(plotter, well, roster)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("Title") == 6
    assert texts.count("Date") == 6
    assert "Agenda" not in texts
    assert "Action items" not in texts
    assert "Attendees" not in texts
    assert "01" not in texts
    assert "P" not in texts
    assert "Todo" not in texts

    seats = meeting_index_covers(well, 6)
    frames = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and not op[1].w == pytest.approx(TICK)
    ]
    for seat in seats:
        assert any(
            box.x == pytest.approx(seat.x)
            and box.y == pytest.approx(seat.y)
            and box.w == pytest.approx(seat.w)
            and box.h == pytest.approx(seat.h)
            for box in (op[1] for op in frames)
        )

    link_ops = [op for op in plotter.ops if op[0] == "link"]
    assert [(op[1], op[2]) for op in link_ops] == [
        (seat, cover.dest) for seat, cover in zip(seats, roster.covers, strict=True)
    ]
    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []

    chrome = RecordingPlotter()
    chrome.begin_page()
    PlannerLayout().paint(page, chrome, NOMAD)
    chrome_texts = [op[2] for op in chrome.ops if op[0] == "text"]
    assert "Meetings" in chrome_texts
    assert "Meet" in chrome_texts
    assert "2026" in chrome_texts
    assert "Agenda" not in chrome_texts
    assert strip_active(page.kind) == "Meet"
    assert dict(strip_items(page))["Meet"] == spec.meetings_index_dest


def test_meeting_dest_header_chip_returns_to_index():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.dest == "meeting-2026-01")
    chrome = RecordingPlotter()
    chrome.begin_page()
    PlannerLayout().paint(page, chrome, NOMAD)
    labels = [op[2] for op in chrome.ops if op[0] == "text"]
    assert "Meeting" in labels
    assert "01" in labels
    assert "Index" not in labels
    assert "Meet" in labels
    assert "Action items" in labels
    assert "Attendees" not in labels
    assert strip_active(page.kind) == "Meet"
    assert dict(strip_items(page))["Meet"] == spec.meetings_index_dest
    leaf_links = [op[2] for op in chrome.ops if op[0] == "link"]
    chip_links = [dest for dest in leaf_links if dest == spec.meetings_index_dest]
    assert len(chip_links) >= 2
    assert spec.dest_for_meeting(1) not in leaf_links


def test_meeting_covers_knob():
    spec = Spec(notes_pages=1, meeting_covers=4)
    pages = YearPlanner().pages(spec)
    roster = next(
        item
        for page in pages
        if page.kind == "meetings_index"
        for item in page.components
        if isinstance(item, MeetingsIndex)
    )
    assert len(roster.covers) == 4
    dests = [page.dest for page in pages]
    assert "meeting-2026-04" in dests
    assert "meeting-2026-05" not in dests
    plotter = RecordingPlotter()
    paint_meetings_index_covers(plotter, well_rect(NOMAD), roster)
    assert [op[2] for op in plotter.ops if op[0] == "link"] == [
        f"meeting-2026-{slot:02d}" for slot in range(1, 5)
    ]
    seats = meeting_index_covers(well_rect(NOMAD), 4)
    assert len(seats) == 4
    assert seats[2].y > seats[0].bottom
    assert math.ceil(4 / COVER_COLS) == 2


def test_meeting_index_pages_knob():
    spec = Spec(notes_pages=1, meeting_index_pages=2)
    assert spec.meeting_count == 12
    pages = YearPlanner().pages(spec)
    dests = [page.dest for page in pages]
    assert dests[12:14] == [
        "meetings-index-2026-01",
        "meetings-index-2026-02",
    ]
    assert dests[14:26] == [f"meeting-2026-{slot:02d}" for slot in range(1, 13)]
    assert dests[26] == "quarter-2026-Q1"

    indexes = [page for page in pages if page.kind == "meetings_index"]
    assert len(indexes) == 2
    slices = [
        [
            cover.number
            for cover in next(
                item for item in page.components if isinstance(item, MeetingsIndex)
            ).covers
        ]
        for page in indexes
    ]
    assert slices == [list(range(1, 7)), list(range(7, 13))]

    page_two = next(item for item in indexes[1].components if isinstance(item, MeetingsIndex))
    plotter = RecordingPlotter()
    paint_meetings_index_covers(plotter, well_rect(NOMAD), page_two)
    assert [op[2] for op in plotter.ops if op[0] == "link"] == [
        f"meeting-2026-{slot:02d}" for slot in range(7, 13)
    ]

    leaf = next(page for page in pages if page.dest == "meeting-2026-08")
    agenda = next(item for item in leaf.components if isinstance(item, MeetingAgenda))
    assert agenda.number == 8
    assert agenda.index_dest == "meetings-index-2026-02"
    assert dict(strip_items(leaf))["Meet"] == "meetings-index-2026-02"
    chrome = RecordingPlotter()
    chrome.begin_page()
    PlannerLayout().paint(leaf, chrome, NOMAD)
    labels = [op[2] for op in chrome.ops if op[0] == "text"]
    assert "08" in labels
    assert "Index" not in labels
    assert "meetings-index-2026-02" in [op[2] for op in chrome.ops if op[0] == "link"]
    assert "meetings-index-2026-01" not in [op[2] for op in chrome.ops if op[0] == "link"]

    year = next(page for page in pages if page.kind == "annual")
    assert dict(strip_items(year))["Meet"] == spec.meetings_index_dest
    assert spec.meetings_index_dest == "meetings-index-2026-01"


def test_meeting_knobs_paint():
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


def test_meeting_section_matches_book():
    spec = Spec(notes_pages=1)
    section = MeetingSection(spec).pages()
    book = [page for page in YearPlanner().pages(spec) if page.kind in {"meetings_index", "meeting"}]
    assert [page.dest for page in section] == [page.dest for page in book]
