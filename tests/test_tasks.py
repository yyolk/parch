from datetime import date, timedelta

import pytest

from parch.books import YearPlanner
from parch.calendar import short_date_range
from parch.components import TasksIndex, WeekTasks
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    TASK_GAP,
    TASK_HEAD_COL_GAP,
    TASK_INDEX_COL_GAP,
    TASK_INDEX_GAP,
    TASK_INDEX_MARK_H,
    TASK_INDEX_MARK_W,
    TASK_INDEX_STUB_GAP,
    TASK_INDEX_STUB_W,
    TASK_INDEX_WEIGHTS,
    TICK,
    checklist_content_height,
    paint_tasks_index_roster,
    paint_week_tasks,
    strip_active,
    strip_items,
    task_index_link_hits,
    task_index_row_parts,
    task_index_row_seats,
    task_week_label,
    tasks_index_roster,
    week_tasks_head_height,
    week_tasks_head_seats,
    week_tasks_seats,
)
from parch.plotter import RecordingPlotter
from parch.sections.tasks import TasksSection
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
    ("Task", "tasks-index-2026"),
    ("Week", "week-2026-W01"),
    ("Day", "2026-01-01"),
    ("Notes", "2026-01-01-notes-1"),
)

_W01_RANGE = short_date_range(date(2025, 12, 29), date(2026, 1, 4))
_W02_RANGE = short_date_range(date(2026, 1, 5), date(2026, 1, 11))


def test_tasks_after_meetings_in_year_book():
    spec = Spec(notes_pages=1)
    pages = YearPlanner().pages(spec)
    dests = [page.dest for page in pages]
    assert dests[12] == "meetings-index-2026"
    assert dests[13:29] == [f"meeting-2026-{slot:02d}" for slot in range(1, 17)]
    assert dests[29] == "tasks-index-2026"
    assert dests[30:33] == [
        "tasks-index-2026-02",
        "tasks-index-2026-03",
        "tasks-index-2026-04",
    ]
    assert dests[33:86] == [f"tasks-2026-W{week:02d}" for week in range(1, 54)]
    assert dests[86] == "quarter-2026-Q1"
    assert [page.kind for page in pages].count("tasks_index") == 4
    assert [page.kind for page in pages].count("task") == 53


def test_tasks_index_page():
    spec = Spec(notes_pages=1)
    page = next(p for p in TasksSection(spec).pages() if p.kind == "tasks_index")
    assert page.dest == "tasks-index-2026"
    assert page.title == "Tasks"
    roster = next(item for item in page.components if isinstance(item, TasksIndex))
    assert roster.year == 2026
    assert roster.dest == "tasks-index-2026"
    assert len(roster.weeks) == 16
    assert [week.iso_week for week in roster.weeks] == list(range(1, 17))
    assert [week.dest for week in roster.weeks] == [
        f"tasks-2026-W{week:02d}" for week in range(1, 17)
    ]
    assert roster.weeks[0].monday == date(2025, 12, 29)
    assert roster.weeks[0].sunday == date(2026, 1, 4)
    assert strip_active(page.kind) == "Task"
    assert strip_items(page) == _TASK_STRIP


def test_tasks_dest_page():
    spec = Spec(notes_pages=1)
    page = next(p for p in TasksSection(spec).pages() if p.dest == "tasks-2026-W03")
    assert page.kind == "task"
    assert page.title == "Tasks"
    well = next(item for item in page.components if isinstance(item, WeekTasks))
    assert well.year == 2026
    assert well.iso_week == 3
    assert well.monday == date(2026, 1, 12)
    assert well.sunday == date(2026, 1, 18)
    assert well.tasks == 7
    assert well.index_dest == "tasks-index-2026"
    assert strip_active(page.kind) == "Task"
    assert strip_items(page) == _TASK_STRIP
    assert ("Task", "tasks-index-2026") in strip_items(page)


def test_week_tasks_seats_stack():
    well = well_rect(NOMAD)
    head, tasks, notes = week_tasks_seats(well, 7)
    assert head.y == pytest.approx(well.y)
    assert head.h == pytest.approx(week_tasks_head_height())
    assert head.x == pytest.approx(well.x)
    assert head.w == pytest.approx(well.w)
    assert tasks.y == pytest.approx(head.bottom + TASK_GAP)
    assert tasks.h == pytest.approx(checklist_content_height(7))
    assert tasks.w == pytest.approx(well.w)
    assert notes.y == pytest.approx(tasks.bottom + TASK_GAP)
    assert notes.bottom == pytest.approx(well.bottom)
    assert notes.w == pytest.approx(well.w)
    assert notes.h > tasks.h
    assert notes.h > well.h * 0.4

    label, dated = week_tasks_head_seats(head)
    assert label.y == pytest.approx(dated.y)
    assert label.h == pytest.approx(dated.h)
    assert dated.x == pytest.approx(label.right + TASK_HEAD_COL_GAP)
    assert dated.w > label.w


def test_week_tasks_paint_template():
    page = WeekTasks(
        year=2026,
        iso_week=1,
        monday=date(2025, 12, 29),
        sunday=date(2026, 1, 4),
        tasks=7,
        index_dest="tasks-index-2026",
    )
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_week_tasks(plotter, well, page)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("W01") == 1
    assert _W01_RANGE in texts
    assert texts.count("Tasks") == 1
    assert texts.count("Notes") == 1
    assert "Agenda" not in texts
    assert "Action items" not in texts
    assert "Attendees" not in texts
    assert "P" not in texts
    assert "Todo" not in texts
    assert "Focus" not in texts
    assert "Title" not in texts
    assert "Date" not in texts

    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 7

    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []


def test_week_tasks_knobs():
    page = WeekTasks(
        year=2026,
        iso_week=2,
        monday=date(2026, 1, 5),
        sunday=date(2026, 1, 11),
        tasks=5,
    )
    plotter = RecordingPlotter()
    paint_week_tasks(plotter, Rect(4, 20, 110, 90), page)
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 5
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Tasks" in texts
    assert "W02" in texts
    assert _W02_RANGE in texts


def test_tasks_header_year_chip_and_task_tab():
    spec = Spec(notes_pages=1)
    page = next(p for p in TasksSection(spec).pages() if p.dest == "tasks-2026-W01")
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Tasks" in texts
    assert "2026" in texts
    assert "W01" in texts
    assert "Projects" not in texts
    assert "Meetings" not in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Proj", "Meet", "Task", "Week", "Day", "Notes"):
        assert label in texts
    assert texts.count("Notes") == 2
    assert strip_active(page.kind) == "Task"
    links = [op[2] for op in plotter.ops if op[0] == "link"]
    assert links.count("tasks-index-2026") >= 2


def test_tasks_index_seats():
    well = well_rect(NOMAD)
    seats = tasks_index_roster(well, 16)
    assert len(seats) == 16
    assert seats[0].y == pytest.approx(well.y)
    assert seats[0].x == pytest.approx(well.x)
    assert seats[0].w == pytest.approx(well.w)
    assert seats[-1].bottom == pytest.approx(well.bottom)
    assert seats[1].y > seats[0].bottom
    leftover = well.h - TASK_INDEX_GAP * 15
    assert seats[0].h == pytest.approx(leftover / 16)

    stub, body = task_index_row_parts(seats[0])
    assert stub.x > seats[0].x
    assert stub.w == pytest.approx(TASK_INDEX_STUB_W)
    assert body.x == pytest.approx(stub.right + TASK_INDEX_STUB_GAP)
    assert body.right < seats[0].right

    dated, title = task_index_row_seats(seats[0])
    assert dated.x == pytest.approx(body.x)
    assert title.right == pytest.approx(body.right)
    assert dated.x > stub.right
    assert dated.right < title.x
    assert title.x == pytest.approx(dated.right + TASK_INDEX_COL_GAP)
    share = dated.w + title.w
    assert dated.w / share == pytest.approx(TASK_INDEX_WEIGHTS[0] / sum(TASK_INDEX_WEIGHTS))
    assert title.w > dated.w
    assert dated.y == pytest.approx(title.y)
    assert dated.bottom == pytest.approx(title.bottom)
    hits = task_index_link_hits(seats[0])
    assert hits == (stub,)
    assert not _rects_overlap(hits[0], dated)
    assert not _rects_overlap(hits[0], title)


def test_tasks_index_paint_range_cues_and_links():
    spec = Spec(notes_pages=1)
    page = next(p for p in TasksSection(spec).pages() if p.kind == "tasks_index")
    roster = next(item for item in page.components if isinstance(item, TasksIndex))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_tasks_index_roster(plotter, well, roster)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert _W01_RANGE in texts
    assert _W02_RANGE in texts
    for week in range(1, 17):
        assert task_week_label(week) in texts
    assert "Title" not in texts
    assert "Date" not in texts
    assert "Attendees" not in texts
    assert "Agenda" not in texts
    assert "P" not in texts
    assert "Todo" not in texts

    marks = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[2]
        and not op[3]
        and op[1].w == pytest.approx(TASK_INDEX_MARK_W)
        and op[1].h == pytest.approx(TASK_INDEX_MARK_H)
    ]
    assert len(marks) == 16

    seats = tasks_index_roster(well, 16)
    rules = [op for op in plotter.ops if op[0] == "line" and op[5] == pytest.approx(0.12)]
    assert len(rules) == 16
    for seat in seats:
        dated, title = task_index_row_seats(seat)
        assert dated.bottom == pytest.approx(title.bottom)

    link_ops = [op for op in plotter.ops if op[0] == "link"]
    expected_hits: list[tuple[Rect, str]] = []
    for seat, week in zip(seats, roster.weeks, strict=True):
        hits = task_index_link_hits(seat)
        assert len(hits) == 1
        stub, body = task_index_row_parts(seat)
        dated, title = task_index_row_seats(seat)
        assert hits[0] == stub
        assert hits[0] != seat
        assert hits[0] != body
        assert not _rects_overlap(hits[0], dated)
        assert not _rects_overlap(hits[0], title)
        expected_hits.append((hits[0], week.dest))
    assert [(op[1], op[2]) for op in link_ops] == expected_hits
    assert [dest for _, dest in expected_hits] == [
        f"tasks-2026-W{week:02d}" for week in range(1, 17)
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


def test_tasks_rows_knob():
    spec = Spec(notes_pages=1, task_index_rows=12)
    assert spec.task_index_pages == 5
    pages = TasksSection(spec).pages()
    index = next(p for p in pages if p.kind == "tasks_index")
    roster = next(item for item in index.components if isinstance(item, TasksIndex))
    assert len(roster.weeks) == 12
    dests = [page.dest for page in pages]
    assert dests[0] == "tasks-index-2026"
    assert dests[1:5] == [
        "tasks-index-2026-02",
        "tasks-index-2026-03",
        "tasks-index-2026-04",
        "tasks-index-2026-05",
    ]
    assert dests[5:] == [f"tasks-2026-W{week:02d}" for week in range(1, 54)]
    plotter = RecordingPlotter()
    paint_tasks_index_roster(plotter, well_rect(NOMAD), roster)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    for week in range(1, 13):
        assert task_week_label(week) in texts
    assert "W13" not in texts
    assert [op[2] for op in plotter.ops if op[0] == "link"] == [
        f"tasks-2026-W{week:02d}" for week in range(1, 13)
    ]
    well = well_rect(NOMAD)
    seats = tasks_index_roster(well, 12)
    link_boxes = [op[1] for op in plotter.ops if op[0] == "link"]
    assert link_boxes == [task_index_link_hits(seat)[0] for seat in seats]


def test_tasks_index_pages_owning_chip():
    spec = Spec(notes_pages=1)
    pages = YearPlanner().pages(spec)
    indexes = [page for page in pages if page.kind == "tasks_index"]
    assert [page.dest for page in indexes] == [
        "tasks-index-2026",
        "tasks-index-2026-02",
        "tasks-index-2026-03",
        "tasks-index-2026-04",
    ]
    slices = [
        [week.iso_week for week in next(item for item in page.components if isinstance(item, TasksIndex)).weeks]
        for page in indexes
    ]
    assert slices == [list(range(1, 17)), list(range(17, 33)), list(range(33, 49)), list(range(49, 54))]

    leaf = next(page for page in pages if page.dest == "tasks-2026-W17")
    well = next(item for item in leaf.components if isinstance(item, WeekTasks))
    assert well.iso_week == 17
    assert well.index_dest == "tasks-index-2026-02"
    assert dict(strip_items(leaf))["Task"] == "tasks-index-2026-02"
    chrome = RecordingPlotter()
    chrome.begin_page()
    PlannerLayout().paint(leaf, chrome, NOMAD)
    labels = [op[2] for op in chrome.ops if op[0] == "text"]
    assert "W17" in labels
    assert "tasks-index-2026-02" in [op[2] for op in chrome.ops if op[0] == "link"]
    assert "tasks-index-2026" not in [op[2] for op in chrome.ops if op[0] == "link"]

    year = next(page for page in pages if page.kind == "annual")
    assert dict(strip_items(year))["Task"] == spec.tasks_index_dest
    assert spec.tasks_index_dest == "tasks-index-2026"


def test_january_only_is_one_index_and_five_weeks():
    spec = Spec(notes_pages=1, months=(1,))
    assert spec.task_week_count == 5
    assert spec.task_index_pages == 1
    pages = TasksSection(spec).pages()
    dests = [page.dest for page in pages]
    assert dests[0] == "tasks-index-2026"
    assert dests[1:] == [f"tasks-2026-W{week:02d}" for week in range(1, 6)]
    assert "tasks-index-2026-02" not in dests
    roster = next(item for item in pages[0].components if isinstance(item, TasksIndex))
    assert [week.iso_week for week in roster.weeks] == [1, 2, 3, 4, 5]
    assert roster.weeks[0].monday == date(2025, 12, 29)
    assert roster.weeks[-1].sunday == date(2026, 2, 1)
    assert spec.dest_for_tasks_index_of(date(2026, 1, 15)) == "tasks-index-2026"
    assert spec.dest_for_task_week(date(2025, 12, 29)) == "tasks-2026-W01"


def test_task_week_label():
    assert task_week_label(1) == "W01"
    assert task_week_label(53) == "W53"
    monday = date(2026, 1, 5)
    assert monday + timedelta(days=6) == date(2026, 1, 11)
