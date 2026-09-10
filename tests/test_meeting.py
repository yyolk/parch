import pytest

from parch.books import YearPlanner
from parch.components import MeetingAgenda, MeetingIndex, ProjectsBoard
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    GHOST,
    INK,
    MEET_GAP,
    MEET_HEAD_COL_GAP,
    MEET_INDEX_BAND_GAP,
    MEET_INDEX_BAND_LABELS,
    MEET_INDEX_HEAD_INKS,
    MEET_INDEX_SPINE_W,
    MEET_LABEL_W,
    MEET_WRITE_LABEL_H,
    MUTED,
    TICK,
    WASH,
    checklist_content_height,
    meeting_head_height,
    meeting_head_seats,
    meeting_seats,
    meetings_index_band_seats,
    meetings_index_bands,
    paint_meeting,
    paint_meetings_index_weeks,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.sections.meeting import (
    MEET_ACTION_ITEMS,
    MEET_AGENDA,
    MEET_INDEX_ROWS,
    MeetingSection,
)
from parch.spec import Spec

_MEET_STRIP = (
    ("Year", "year-2026"),
    ("Quar", "quarter-2026-Q1"),
    ("Mon", "month-2026-01"),
    ("Habit", "month-2026-01-habits"),
    ("Proj", "projects-index-2026-01"),
    ("Meet", "meetings-index-weeks-2026"),
    ("Week", "week-2026-W01"),
    ("Day", "2026-01-01"),
    ("Notes", "2026-01-01-notes-1"),
)


def _index_page(spec: Spec | None = None):
    spec = spec or Spec(notes_pages=1)
    return MeetingSection(spec).pages()[0]


def test_meeting_not_in_year_book():
    kinds = [page.kind for page in YearPlanner().pages(Spec(notes_pages=1))]
    dests = [page.dest for page in YearPlanner().pages(Spec(notes_pages=1))]
    assert kinds.count("projects") == 1
    assert "meeting" not in kinds
    assert "meetings_index" not in kinds
    assert "meetings-index-weeks-2026" not in dests
    assert "meeting-2026-01" not in dests
    page = next(p for p in YearPlanner().pages(Spec(notes_pages=1)) if p.kind == "projects")
    assert any(isinstance(item, ProjectsBoard) for item in page.components)
    assert not any(isinstance(item, MeetingAgenda) for item in page.components)
    assert not any(isinstance(item, MeetingIndex) for item in page.components)
    assert "Meet" not in (label for label, _ in strip_items(page))


def test_meetings_index_weeks_page_and_dests():
    spec = Spec(notes_pages=1)
    pages = MeetingSection(spec).pages()
    assert len(pages) == 1 + 3 * MEET_INDEX_ROWS
    index = pages[0]
    assert index.dest == "meetings-index-weeks-2026"
    assert index.kind == "meetings_index"
    assert index.title == "Meetings"
    board = next(item for item in index.components if isinstance(item, MeetingIndex))
    assert board.year == 2026
    assert board.dest == index.dest
    assert [band.label for band in board.bands] == list(MEET_INDEX_BAND_LABELS)
    assert MEET_INDEX_BAND_LABELS == ("This week", "Next week", "Later")
    assert [band.dated for band in board.bands] == [True, True, False]
    assert all(len(band.rows) == MEET_INDEX_ROWS for band in board.bands)

    dests = [page.dest for page in pages[1:]]
    assert dests == [f"meeting-2026-{n:02d}" for n in range(1, 3 * MEET_INDEX_ROWS + 1)]
    assert dests == [row.dest for band in board.bands for row in band.rows]
    dest = pages[1]
    assert dest.kind == "meeting"
    assert dest.title == "Meeting"
    agenda = next(item for item in dest.components if isinstance(item, MeetingAgenda))
    assert agenda.year == 2026
    assert agenda.agenda == 4
    assert agenda.action_items == 3
    assert not hasattr(agenda, "attendees")
    assert agenda.index_dest == index.dest
    assert agenda.number == 1
    assert MEET_AGENDA == 4
    assert MEET_ACTION_ITEMS == 3


def test_meet_tab_points_at_index():
    spec = Spec(notes_pages=1)
    pages = MeetingSection(spec).pages()
    index = pages[0]
    dest = pages[1]
    assert strip_items(index) == _MEET_STRIP
    assert strip_items(dest) == _MEET_STRIP
    assert strip_active(index.kind) == "Meet"
    assert strip_active(dest.kind) == "Meet"
    assert strip_active("projects") == ""


def test_meetings_index_band_tracks():
    well = well_rect(NOMAD)
    bands = meetings_index_bands(well)
    assert len(bands) == 3
    assert bands[0].y == pytest.approx(well.y)
    assert bands[0].x == pytest.approx(well.x)
    assert bands[0].w == pytest.approx(well.w)
    assert bands[-1].bottom == pytest.approx(well.bottom)
    assert bands[1].y == pytest.approx(bands[0].bottom + MEET_INDEX_BAND_GAP)
    leftover = well.h - 2 * MEET_INDEX_BAND_GAP
    assert bands[0].h == pytest.approx(leftover / 3)
    assert bands[1].h == pytest.approx(bands[0].h)
    assert bands[2].h == pytest.approx(bands[0].h)

    head, lines = meetings_index_band_seats(bands[0], 4)
    assert len(lines) == 4
    assert head.y > bands[0].y
    assert lines[0].y > head.bottom
    assert lines[-1].bottom <= bands[0].bottom
    assert lines[0].x > bands[0].x
    assert lines[0].right < bands[0].right

    five_head, five = meetings_index_band_seats(bands[0], 5)
    assert len(five) == 5
    assert five_head.h == pytest.approx(head.h)


def test_meetings_index_weeks_paint_hierarchy_ticks_and_links():
    spec = Spec(notes_pages=1)
    page = _index_page(spec)
    board = next(item for item in page.components if isinstance(item, MeetingIndex))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_meetings_index_weeks(plotter, well, board)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("This week") == 1
    assert texts.count("Next week") == 1
    assert texts.count("Later") == 1
    assert "Attendees" not in texts
    assert "Active" not in texts
    assert "Waiting" not in texts
    assert "Done" not in texts
    assert "P" not in texts
    assert "Focus" not in texts
    assert "Agenda" not in texts

    this_week = next(op for op in plotter.ops if op[0] == "text" and op[2] == "This week")
    next_week = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Next week")
    later = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Later")
    assert this_week[5] is True
    assert this_week[7] == pytest.approx(INK)
    assert next_week[5] is False
    assert next_week[7] == pytest.approx(MUTED)
    assert later[5] is False
    assert later[7] == pytest.approx(GHOST)
    assert MEET_INDEX_HEAD_INKS == (INK, MUTED, GHOST)

    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 3 * MEET_INDEX_ROWS

    washes = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[3] and op[5] == pytest.approx(WASH)
    ]
    assert len(washes) == 1
    assert washes[0][1].w == pytest.approx(well.w)

    spines = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[3] and op[1].w == pytest.approx(MEET_INDEX_SPINE_W)
    ]
    assert len(spines) == 1

    outlines = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(well.w)
    ]
    assert len(outlines) == 3

    links = plotter.links()
    assert links == [f"meeting-2026-{n:02d}" for n in range(1, 3 * MEET_INDEX_ROWS + 1)]
    hits = [op[1] for op in plotter.ops if op[0] == "link"]
    assert all(hit.w > 20 for hit in hits)


def test_meetings_index_weeks_knobs():
    spec = Spec(notes_pages=1, meeting_index_rows=5)
    pages = MeetingSection(spec).pages()
    assert len(pages) == 1 + 15
    board = next(item for item in pages[0].components if isinstance(item, MeetingIndex))
    assert all(len(band.rows) == 5 for band in board.bands)
    plotter = RecordingPlotter()
    paint_meetings_index_weeks(plotter, Rect(4, 20, 110, 90), board)
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 15
    assert plotter.links()[-1] == "meeting-2026-15"


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


def test_index_header_year_and_meet_tab():
    spec = Spec(notes_pages=1)
    page = _index_page(spec)
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Meetings" in texts
    assert "2026" in texts
    assert "Meet" in texts
    assert "This week" in texts
    assert "Next week" in texts
    assert "Later" in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Proj", "Week", "Day", "Notes"):
        assert label in texts
    assert MEET_INDEX_ROWS == 4


def test_meeting_dest_back_link_and_locked_well():
    spec = Spec(notes_pages=1)
    pages = MeetingSection(spec).pages()
    dest = pages[1]
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(dest, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Meeting" in texts
    assert "2026" in texts
    assert "01" in texts
    assert "Meet" in texts
    assert "Attendees" not in texts
    assert "Action items" in texts
    links = plotter.links()
    assert "meetings-index-weeks-2026" in links
    assert links.count("meetings-index-weeks-2026") >= 2

    well_plotter = RecordingPlotter()
    agenda = next(item for item in dest.components if isinstance(item, MeetingAgenda))
    paint_meeting(well_plotter, well_rect(NOMAD), agenda)
    ticks = [
        op
        for op in well_plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 4 + 3


def test_experiment_pages_reserve_and_link():
    spec = Spec(notes_pages=1)
    pages = MeetingSection(spec).pages()
    plotter = RecordingPlotter()
    for page in pages:
        plotter.reserve_dest(page.dest)
    for page in pages:
        plotter.begin_page()
        plotter.add_dest(page.dest)
        PlannerLayout().paint(page, plotter, NOMAD)
    dests = plotter.dests()
    assert dests[0] == "meetings-index-weeks-2026"
    assert "meeting-2026-01" in dests
    assert "meeting-2026-12" in dests
    links = plotter.links()
    assert "meeting-2026-01" in links
    assert "meeting-2026-12" in links
    assert "meetings-index-weeks-2026" in links
