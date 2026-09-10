import pytest

from parch.books import YearPlanner
from parch.components import TasksIndex, WeekTasks
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    MEET_HEAD_COL_GAP,
    MEET_LABEL_W,
    MEET_WRITE_LABEL_H,
    TASK_BAND_GAP,
    TASK_GAP,
    TASK_PREVIEW_TICK,
    TASK_TICKET_WRITE_PAD,
    TICK,
    TICKET_MARK,
    TICKET_STUB_W,
    checklist_content_height,
    meeting_head_height,
    paint_tasks_index_tickets,
    paint_week_tasks,
    strip_active,
    strip_items,
    task_ticket_body_seats,
    task_ticket_link_hits,
    task_ticket_parts,
    task_ticket_preview_bands,
    task_ticket_seats,
    task_ticket_write_in,
    week_tasks_band_seats,
    week_tasks_head_seats,
    week_tasks_seats,
)
from parch.plotter import RecordingPlotter
from parch.sections.tasks import TASK_CARRY, TASK_ROWS, TasksSection
from parch.spec import Spec


def _rects_overlap(a: Rect, b: Rect) -> bool:
    return a.x < b.right and b.x < a.right and a.y < b.bottom and b.y < a.bottom


_TASK_STRIP = (
    ("Year", "year-2026"),
    ("Quar", "quarter-2026-Q1"),
    ("Mon", "month-2026-01"),
    ("Habit", "month-2026-01-habits"),
    ("Proj", "projects-index-2026-01"),
    ("Meet", "meetings-index-2026"),
    ("Task", "tasks-index-2026-01"),
    ("Week", "week-2026-W01"),
    ("Day", "2026-01-01"),
    ("Notes", "2026-01-01-notes-1"),
)


def test_tasks_after_meetings_in_year_book():
    spec = Spec(notes_pages=1)
    pages = YearPlanner().pages(spec)
    dests = [page.dest for page in pages]
    assert dests[2] == "projects-2026"
    assert dests[3] == "projects-index-2026-01"
    assert dests[12] == "meetings-index-2026"
    assert dests[13:29] == [f"meeting-2026-{slot:02d}" for slot in range(1, 17)]
    assert dests[29] == "tasks-index-2026-01"
    assert dests[30:38] == [f"tasks-2026-{slot:02d}" for slot in range(1, 9)]
    assert dests[38] == "quarter-2026-Q1"
    assert [page.kind for page in pages].count("tasks_index") == 1
    assert [page.kind for page in pages].count("task") == 8


def test_tasks_index_page():
    spec = Spec(notes_pages=1)
    page = next(p for p in TasksSection(spec).pages() if p.kind == "tasks_index")
    assert page.dest == "tasks-index-2026-01"
    assert page.title == "Tasks"
    roster = next(item for item in page.components if isinstance(item, TasksIndex))
    assert roster.year == 2026
    assert roster.dest == "tasks-index-2026-01"
    assert len(roster.tickets) == 8
    assert [ticket.number for ticket in roster.tickets] == list(range(1, 9))
    assert [ticket.dest for ticket in roster.tickets] == [
        f"tasks-2026-{slot:02d}" for slot in range(1, 9)
    ]
    assert strip_active(page.kind) == "Task"
    assert strip_items(page) == _TASK_STRIP


def test_tasks_dest_page():
    spec = Spec(notes_pages=1)
    page = next(p for p in TasksSection(spec).pages() if p.dest == "tasks-2026-03")
    assert page.kind == "task"
    assert page.title == "Tasks"
    week = next(item for item in page.components if isinstance(item, WeekTasks))
    assert week.year == 2026
    assert week.tasks == 8
    assert week.carry == 3
    assert week.number == 3
    assert week.index_dest == "tasks-index-2026-01"
    assert TASK_ROWS == 8
    assert TASK_CARRY == 3
    assert strip_active(page.kind) == "Task"
    assert strip_items(page) == _TASK_STRIP
    assert ("Task", "tasks-index-2026-01") in strip_items(page)


def test_week_tasks_seats_stack():
    well = well_rect(NOMAD)
    head, tasks, notes, band = week_tasks_seats(well, 8, 3)
    assert head.y == pytest.approx(well.y)
    assert head.h == pytest.approx(meeting_head_height())
    assert head.x == pytest.approx(well.x)
    assert head.w == pytest.approx(well.w)
    assert tasks.y == pytest.approx(head.bottom + TASK_GAP)
    assert tasks.h == pytest.approx(checklist_content_height(8))
    assert tasks.w == pytest.approx(well.w)
    assert notes.y == pytest.approx(tasks.bottom + TASK_GAP)
    assert notes.w == pytest.approx(well.w)
    assert band.y == pytest.approx(notes.bottom + TASK_GAP)
    assert band.bottom == pytest.approx(well.bottom)
    assert band.h == pytest.approx(checklist_content_height(3))
    assert band.w == pytest.approx(well.w)
    assert notes.h > tasks.h
    assert notes.h > band.h
    assert notes.h > well.h * 0.3

    title, dated = week_tasks_head_seats(head)
    assert title.y == pytest.approx(dated.y)
    assert title.h == pytest.approx(dated.h)
    assert title.bottom == pytest.approx(dated.bottom)
    assert dated.x == pytest.approx(title.right + MEET_HEAD_COL_GAP)
    assert title.w > dated.w
    assert MEET_LABEL_W < title.w / 3

    done, carry = week_tasks_band_seats(band)
    assert done.y == pytest.approx(carry.y)
    assert done.h == pytest.approx(carry.h)
    assert carry.x == pytest.approx(done.right + TASK_BAND_GAP)
    assert done.w == pytest.approx(carry.w)


def test_week_tasks_paint_template():
    week = WeekTasks(year=2026, tasks=8, carry=3, index_dest="tasks-index-2026-01", number=1)
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_week_tasks(plotter, well, week)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("Week") == 1
    assert texts.count("Range") == 1
    assert texts.count("Tasks") == 1
    assert texts.count("Notes") == 1
    assert texts.count("Done") == 1
    assert texts.count("Carry") == 1
    assert "Attendees" not in texts
    assert "Agenda" not in texts
    assert "Action items" not in texts
    assert "P" not in texts
    assert "Todo" not in texts
    assert "Doing" not in texts
    assert "Projects" not in texts
    for rejected in ("PROJECT", "Focus", "This week", "This month", "Someday"):
        assert rejected not in texts

    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 8 + 3 + 3

    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []

    week_box = next(op[1] for op in plotter.ops if op[0] == "text" and op[2] == "Week")
    range_box = next(op[1] for op in plotter.ops if op[0] == "text" and op[2] == "Range")
    assert week_box.h == pytest.approx(MEET_WRITE_LABEL_H)
    assert range_box.h == pytest.approx(MEET_WRITE_LABEL_H)
    rules = [
        op
        for op in plotter.ops
        if op[0] == "line" and op[2] == pytest.approx(week_box.bottom)
    ]
    assert len(rules) >= 2
    assert week_box.bottom == pytest.approx(range_box.bottom)


def test_week_tasks_knobs():
    week = WeekTasks(year=2026, tasks=6, carry=2)
    plotter = RecordingPlotter()
    paint_week_tasks(plotter, Rect(4, 20, 110, 90), week)
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 6 + 2 + 2
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Tasks" in texts
    assert "Done" in texts
    assert "Carry" in texts
    assert "Agenda" not in texts


def test_task_header_year_chip_and_task_tab():
    spec = Spec(notes_pages=1)
    page = next(p for p in TasksSection(spec).pages() if p.dest == "tasks-2026-01")
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Tasks" in texts
    assert "2026" in texts
    assert "01" in texts
    assert "Projects" not in texts
    assert "Attendees" not in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Proj", "Meet", "Task", "Week", "Day", "Notes"):
        assert label in texts
    assert texts.count("Notes") == 2
    assert "Done" in texts
    assert "Carry" in texts
    assert strip_active(page.kind) == "Task"
    links = [op[2] for op in plotter.ops if op[0] == "link"]
    assert links.count("tasks-index-2026-01") >= 2


def test_task_ticket_seats():
    well = Rect(4, 20, 110, 90)
    seats = task_ticket_seats(well, 8)
    assert len(seats) == 8
    assert seats[0].y == pytest.approx(well.y)
    assert seats[-1].bottom == pytest.approx(well.bottom)
    stub, body = task_ticket_parts(seats[0])
    assert stub.w == pytest.approx(TICKET_STUB_W)
    name, preview = task_ticket_body_seats(body)
    write = task_ticket_write_in(name)
    assert write.x == pytest.approx(name.x)
    assert write.right == pytest.approx(name.right)
    assert write.right < preview.x
    assert write.h == pytest.approx(max(name.h - TASK_TICKET_WRITE_PAD, 1))
    head, tasks, notes, band = task_ticket_preview_bands(preview)
    assert head.y > preview.y
    assert band.bottom < preview.bottom
    assert tasks.y > head.bottom
    assert notes.y > tasks.bottom
    assert band.y > notes.bottom
    assert notes.h > tasks.h
    hits = task_ticket_link_hits(seats[0])
    assert hits == (stub, preview)
    assert not _rects_overlap(hits[0], write)
    assert not _rects_overlap(hits[1], write)


def test_tasks_index_paint_write_in_and_links():
    spec = Spec(notes_pages=1)
    page = next(p for p in TasksSection(spec).pages() if p.kind == "tasks_index")
    roster = next(item for item in page.components if isinstance(item, TasksIndex))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_tasks_index_tickets(plotter, well, roster)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    for slot in range(1, 9):
        assert f"{slot:02d}" in texts
    assert "P" not in texts
    assert "Todo" not in texts
    assert "Attendees" not in texts
    assert "Agenda" not in texts
    assert "Atlas" not in texts

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
        and op[1].w == pytest.approx(TASK_PREVIEW_TICK)
    ]
    assert len(preview_ticks) == 8 * (8 + 3 + 3)

    seats = task_ticket_seats(well, 8)
    rules = [op for op in plotter.ops if op[0] == "line" and op[5] == pytest.approx(0.12)]
    write_rules = []
    for seat in seats:
        _, body = task_ticket_parts(seat)
        name, preview = task_ticket_body_seats(body)
        write = task_ticket_write_in(name)
        matches = [
            op
            for op in rules
            if op[1] == pytest.approx(write.x)
            and op[2] == pytest.approx(write.bottom)
            and op[3] == pytest.approx(write.right)
        ]
        assert len(matches) == 1
        assert matches[0][3] < preview.x
        write_rules.append(matches[0])
    assert len(write_rules) == 8

    link_ops = [op for op in plotter.ops if op[0] == "link"]
    expected_hits: list[tuple[Rect, str]] = []
    for seat, ticket in zip(seats, roster.tickets, strict=True):
        hits = task_ticket_link_hits(seat)
        assert len(hits) == 2
        stub, body = task_ticket_parts(seat)
        name, preview = task_ticket_body_seats(body)
        write = task_ticket_write_in(name)
        assert hits[0] == stub
        assert hits[1] == preview
        for hit in hits:
            assert not _rects_overlap(hit, write)
        expected_hits.extend((hit, ticket.dest) for hit in hits)
    assert [(op[1], op[2]) for op in link_ops] == expected_hits
    assert [dest for _, dest in expected_hits] == [
        dest for slot in range(1, 9) for dest in (f"tasks-2026-{slot:02d}",) * 2
    ]
    for seat in seats:
        assert all(op[1] != seat for op in link_ops)
    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []

    chrome = RecordingPlotter()
    chrome.begin_page()
    PlannerLayout().paint(page, chrome, NOMAD)
    chrome_texts = [op[2] for op in chrome.ops if op[0] == "text"]
    assert "Tasks" in chrome_texts
    assert "Task" in chrome_texts
    assert "2026" in chrome_texts
    assert strip_active(page.kind) == "Task"
    assert dict(strip_items(page))["Task"] == spec.tasks_index_dest


def test_tasks_tickets_knob():
    spec = Spec(notes_pages=1, task_tickets=6)
    pages = TasksSection(spec).pages()
    index = next(p for p in pages if p.kind == "tasks_index")
    roster = next(item for item in index.components if isinstance(item, TasksIndex))
    assert len(roster.tickets) == 6
    dests = [page.dest for page in pages]
    assert dests[0] == "tasks-index-2026-01"
    assert dests[1:] == [f"tasks-2026-{slot:02d}" for slot in range(1, 7)]
    assert "tasks-2026-07" not in dests
    plotter = RecordingPlotter()
    paint_tasks_index_tickets(plotter, well_rect(NOMAD), roster)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    for slot in range(1, 7):
        assert f"{slot:02d}" in texts
    assert "07" not in texts
    assert [op[2] for op in plotter.ops if op[0] == "link"] == [
        dest for slot in range(1, 7) for dest in (f"tasks-2026-{slot:02d}",) * 2
    ]


def test_tasks_index_pages_knob():
    spec = Spec(notes_pages=1, task_index_pages=3)
    assert spec.task_count == 24
    pages = YearPlanner().pages(spec)
    dests = [page.dest for page in pages]
    assert dests[29:32] == [
        "tasks-index-2026-01",
        "tasks-index-2026-02",
        "tasks-index-2026-03",
    ]
    assert dests[32:56] == [f"tasks-2026-{slot:02d}" for slot in range(1, 25)]
    assert dests[56] == "quarter-2026-Q1"

    indexes = [page for page in pages if page.kind == "tasks_index"]
    assert len(indexes) == 3
    slices = [
        [
            ticket.number
            for ticket in next(
                item for item in page.components if isinstance(item, TasksIndex)
            ).tickets
        ]
        for page in indexes
    ]
    assert slices == [list(range(1, 9)), list(range(9, 17)), list(range(17, 25))]

    page_two = next(item for item in indexes[1].components if isinstance(item, TasksIndex))
    plotter = RecordingPlotter()
    paint_tasks_index_tickets(plotter, well_rect(NOMAD), page_two)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "09" in texts
    assert "16" in texts
    assert "01" not in texts
    assert [op[2] for op in plotter.ops if op[0] == "link"] == [
        dest for slot in range(9, 17) for dest in (f"tasks-2026-{slot:02d}",) * 2
    ]

    leaf = next(page for page in pages if page.dest == "tasks-2026-10")
    week = next(item for item in leaf.components if isinstance(item, WeekTasks))
    assert week.number == 10
    assert week.index_dest == "tasks-index-2026-02"
    assert dict(strip_items(leaf))["Task"] == "tasks-index-2026-02"
    chrome = RecordingPlotter()
    chrome.begin_page()
    PlannerLayout().paint(leaf, chrome, NOMAD)
    labels = [op[2] for op in chrome.ops if op[0] == "text"]
    assert "10" in labels
    assert "Index" not in labels
    assert "tasks-index-2026-02" in [op[2] for op in chrome.ops if op[0] == "link"]
    assert "tasks-index-2026-01" not in [op[2] for op in chrome.ops if op[0] == "link"]

    year = next(page for page in pages if page.kind == "annual")
    assert dict(strip_items(year))["Task"] == spec.tasks_index_dest
    assert spec.tasks_index_dest == "tasks-index-2026-01"
