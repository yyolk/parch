from datetime import date

import pytest

from parch.books import YearPlanner
from parch.calendar import short_date_range
from parch.components import TasksIndex, WeeklyTasks
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    TASK_COL_GAP,
    TASK_GAP,
    TASK_INDEX_CHIP_GAP,
    TASK_INDEX_CHIP_W,
    TASK_INDEX_COL_GAP,
    TASK_INDEX_GAP,
    TICK,
    checklist_content_height,
    paint_tasks_index_chips,
    paint_weekly_tasks,
    strip_active,
    strip_items,
    task_index_chip_parts,
    task_index_link_hits,
    tasks_index_seats,
    weekly_tasks_seats,
)
from parch.plotter import RecordingPlotter
from parch.sections.tasks import TASK_LATER, TASK_MORNING, TasksSection
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


def test_tasks_after_meetings_in_year_book():
    spec = Spec(notes_pages=1)
    pages = YearPlanner().pages(spec)
    dests = [page.dest for page in pages]
    assert dests[12] == "meetings-index-2026"
    assert dests[13:29] == [f"meeting-2026-{slot:02d}" for slot in range(1, 17)]
    assert dests[29] == "tasks-index-2026"
    assert dests[30:83] == [f"tasks-2026-W{week:02d}" for week in range(1, 54)]
    assert dests[83] == "quarter-2026-Q1"
    assert [page.kind for page in pages].count("tasks_index") == 1
    assert [page.kind for page in pages].count("tasks") == 53


def test_tasks_index_page():
    spec = Spec(notes_pages=1)
    page = next(p for p in TasksSection(spec).pages() if p.kind == "tasks_index")
    assert page.dest == "tasks-index-2026"
    assert page.title == "Tasks"
    roster = next(item for item in page.components if isinstance(item, TasksIndex))
    assert roster.year == 2026
    assert roster.dest == "tasks-index-2026"
    assert len(roster.weeks) == 53
    assert [week.iso_week for week in roster.weeks] == list(range(1, 54))
    assert [week.dest for week in roster.weeks] == [
        f"tasks-2026-W{week:02d}" for week in range(1, 54)
    ]
    assert roster.weeks[0].monday.isoformat() == "2025-12-29"
    assert roster.weeks[-1].monday.isoformat() == "2026-12-28"
    assert strip_active(page.kind) == "Task"
    assert strip_items(page) == _TASK_STRIP


def test_tasks_dest_page():
    spec = Spec(notes_pages=1)
    page = next(p for p in TasksSection(spec).pages() if p.dest == "tasks-2026-W03")
    assert page.kind == "tasks"
    assert page.title == "Tasks"
    tasks = next(item for item in page.components if isinstance(item, WeeklyTasks))
    assert tasks.year == 2026
    assert tasks.iso_week == 3
    assert tasks.morning == 6
    assert tasks.later == 6
    assert tasks.number == 3
    assert tasks.index_dest == "tasks-index-2026"
    assert TASK_MORNING == 6
    assert TASK_LATER == 6
    assert strip_active(page.kind) == "Task"
    assert ("Task", "tasks-index-2026") in strip_items(page)


def test_tasks_dest_landing_skips_unpressed_monday():
    spec = Spec(notes_pages=1)
    page = next(p for p in TasksSection(spec).pages() if p.dest == "tasks-2026-W01")
    assert ("Day", "2026-01-01") in strip_items(page)
    assert ("Week", "week-2026-W01") in strip_items(page)
    assert ("Task", "tasks-index-2026") in strip_items(page)


def test_weekly_tasks_seats_two_column_plus_leftover():
    well = well_rect(NOMAD)
    morning, later, notes = weekly_tasks_seats(well, 6, 6)
    assert morning.y == pytest.approx(well.y)
    assert later.y == pytest.approx(well.y)
    assert morning.h == pytest.approx(checklist_content_height(6))
    assert later.h == pytest.approx(morning.h)
    assert later.x == pytest.approx(morning.right + TASK_COL_GAP)
    assert morning.w == pytest.approx(later.w)
    assert morning.x == pytest.approx(well.x)
    assert later.right == pytest.approx(well.right)
    assert notes.y == pytest.approx(morning.bottom + TASK_GAP)
    assert notes.x == pytest.approx(well.x)
    assert notes.w == pytest.approx(well.w)
    assert notes.bottom == pytest.approx(well.bottom)
    assert notes.h > well.h * 0.4
    assert notes.h > morning.h


def test_weekly_tasks_paint_template():
    tasks = WeeklyTasks(
        year=2026,
        iso_week=1,
        monday=date(2025, 12, 29),
        sunday=date(2026, 1, 4),
        morning=6,
        later=6,
        index_dest="tasks-index-2026",
        number=1,
    )
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_weekly_tasks(plotter, well, tasks)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("Morning") == 1
    assert texts.count("Later") == 1
    assert texts.count("Notes") == 1
    assert "Focus" not in texts
    assert "Agenda" not in texts
    assert "Action items" not in texts
    assert "Attendees" not in texts
    assert "To do" not in texts
    assert "Doing" not in texts
    assert "Done" not in texts
    assert "Todo" not in texts
    assert "Date" not in texts
    assert "Title" not in texts
    assert "P" not in texts

    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 6 + 6

    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []


def test_weekly_tasks_knobs():
    tasks = WeeklyTasks(
        year=2026,
        iso_week=2,
        monday=date(2026, 1, 5),
        sunday=date(2026, 1, 11),
        morning=4,
        later=5,
    )
    plotter = RecordingPlotter()
    paint_weekly_tasks(plotter, Rect(4, 20, 110, 90), tasks)
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 4 + 5
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Morning" in texts
    assert "Later" in texts
    assert "Focus" not in texts


def test_tasks_header_chip_and_task_tab():
    spec = Spec(notes_pages=1)
    page = next(p for p in TasksSection(spec).pages() if p.dest == "tasks-2026-W05")
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Tasks" in texts
    assert "05" in texts
    assert "Morning" in texts
    assert "Later" in texts
    assert "Focus" not in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Proj", "Meet", "Task", "Week", "Day", "Notes"):
        assert label in texts
    assert texts.count("Notes") == 2
    assert strip_active(page.kind) == "Task"
    links = [op[2] for op in plotter.ops if op[0] == "link"]
    assert links.count("tasks-index-2026") >= 2
    week = next(item for item in page.components if isinstance(item, WeeklyTasks))
    assert short_date_range(week.monday, week.sunday) in texts


def test_tasks_index_seats_two_column():
    well = well_rect(NOMAD)
    seats = tasks_index_seats(well, 53)
    assert len(seats) == 53
    assert seats[0].y == pytest.approx(well.y)
    assert seats[0].x == pytest.approx(well.x)
    assert seats[1].x > seats[0].right
    assert seats[1].y == pytest.approx(seats[0].y)
    assert seats[2].x == pytest.approx(seats[0].x)
    assert seats[2].y > seats[0].bottom
    assert seats[-1].bottom == pytest.approx(well.bottom)
    leftover = well.h - TASK_INDEX_GAP * 26
    assert seats[0].h == pytest.approx(leftover / 27)
    assert seats[1].x == pytest.approx(seats[0].right + TASK_INDEX_COL_GAP)
    assert seats[0].w == pytest.approx(seats[1].w)

    chip, labeled = task_index_chip_parts(seats[0])
    assert chip.w == pytest.approx(TASK_INDEX_CHIP_W)
    assert labeled.x == pytest.approx(chip.right + TASK_INDEX_CHIP_GAP)
    assert labeled.right <= seats[0].right
    hits = task_index_link_hits(seats[0])
    assert hits == (chip,)
    assert not _rects_overlap(hits[0], labeled)


def test_tasks_index_paint_chips_and_links():
    spec = Spec(notes_pages=1)
    page = next(p for p in TasksSection(spec).pages() if p.kind == "tasks_index")
    roster = next(item for item in page.components if isinstance(item, TasksIndex))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_tasks_index_chips(plotter, well, roster)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    for week in range(1, 54):
        assert f"W{week:02d}" in texts
    assert "Date" not in texts
    assert "Title" not in texts
    assert "Focus" not in texts
    assert "Agenda" not in texts
    assert "Morning" not in texts
    assert "P" not in texts
    assert short_date_range(roster.weeks[0].monday, roster.weeks[0].sunday) in texts
    assert short_date_range(roster.weeks[1].monday, roster.weeks[1].sunday) in texts

    chips = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TASK_INDEX_CHIP_W)
    ]
    assert len(chips) == 53

    seats = tasks_index_seats(well, 53)
    link_ops = [op for op in plotter.ops if op[0] == "link"]
    expected_hits: list[tuple[Rect, str]] = []
    for seat, week in zip(seats, roster.weeks, strict=True):
        hits = task_index_link_hits(seat)
        chip, labeled = task_index_chip_parts(seat)
        assert hits[0] == chip
        assert not _rects_overlap(hits[0], labeled)
        expected_hits.append((hits[0], week.dest))
    assert [(op[1], op[2]) for op in link_ops] == expected_hits
    assert [dest for _, dest in expected_hits] == [
        f"tasks-2026-W{week:02d}" for week in range(1, 54)
    ]
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


def test_tasks_weeks_follow_pressed_months():
    spec = Spec(notes_pages=1, months=(1, 2, 3))
    pages = TasksSection(spec).pages()
    index = next(p for p in pages if p.kind == "tasks_index")
    roster = next(item for item in index.components if isinstance(item, TasksIndex))
    assert len(roster.weeks) == 14
    dests = [page.dest for page in pages]
    assert dests[0] == "tasks-index-2026"
    assert dests[1:] == [f"tasks-2026-W{week:02d}" for week in range(1, 15)]
    assert "tasks-2026-W15" not in dests
    plotter = RecordingPlotter()
    paint_tasks_index_chips(plotter, well_rect(NOMAD), roster)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "W01" in texts
    assert "W14" in texts
    assert "W15" not in texts
    assert [op[2] for op in plotter.ops if op[0] == "link"] == [
        f"tasks-2026-W{week:02d}" for week in range(1, 15)
    ]
