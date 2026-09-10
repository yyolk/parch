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
    TASK_GAP,
    TASK_INDEX_FOCUS_GAP,
    TASK_INDEX_FOCUS_WEIGHTS,
    TASK_INDEX_LIST_MARK,
    TASK_INDEX_MARK,
    TICK,
    checklist_content_height,
    paint_tasks_index_focus,
    paint_weekly_tasks,
    strip_active,
    strip_items,
    task_seats,
    tasks_index_focus_parts,
    tasks_index_focus_seats,
    tasks_index_list_row,
)
from parch.plotter import RecordingPlotter
from parch.sections.tasks import TasksSection, planner_task_weeks
from parch.spec import Spec


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


def test_tasks_after_meetings_and_task_nav():
    spec = Spec(notes_pages=1)
    pages = YearPlanner().pages(spec)
    dests = [page.dest for page in pages]
    assert dests[12] == "meetings-index-2026"
    assert dests[29] == "tasks-index-2026"
    assert dests[30:38] == [f"tasks-2026-W{week:02d}" for week in range(1, 9)]
    assert dests[38] == "quarter-2026-Q1"

    index = pages[29]
    assert index.kind == "tasks_index"
    assert index.title == "Tasks"
    assert strip_active(index.kind) == "Task"
    assert strip_items(index) == _TASK_STRIP

    roster = next(item for item in index.components if isinstance(item, TasksIndex))
    assert roster.year == 2026
    assert roster.dest == "tasks-index-2026"
    assert roster.preview == 3
    assert roster.featured.iso_week == 1
    assert roster.featured.dest == "tasks-2026-W01"
    assert roster.featured.monday == date(2025, 12, 29)
    assert roster.featured.sunday == date(2026, 1, 4)
    assert [slot.dest for slot in roster.entries] == [
        f"tasks-2026-W{week:02d}" for week in range(2, 9)
    ]
    assert [slot.iso_week for slot in roster.entries] == list(range(2, 9))

    leaf = next(page for page in pages if page.dest == "tasks-2026-W03")
    assert leaf.kind == "task"
    assert leaf.title == "Tasks"
    assert strip_active(leaf.kind) == "Task"
    assert strip_items(leaf) == _TASK_STRIP
    well = next(item for item in leaf.components if isinstance(item, WeeklyTasks))
    assert well.year == 2026
    assert well.iso_week == 3
    assert well.tasks == 8
    assert well.monday == date(2026, 1, 12)
    assert well.sunday == date(2026, 1, 18)
    assert well.dest == "tasks-2026-W03"
    assert well.index_dest == "tasks-index-2026"


def test_tasks_section_builds_index_and_dests():
    spec = Spec(notes_pages=1)
    pages = TasksSection(spec).pages()
    assert pages[0].dest == "tasks-index-2026"
    assert [page.dest for page in pages[1:]] == [
        f"tasks-2026-W{week:02d}" for week in range(1, 9)
    ]
    assert all(page.kind == "task" for page in pages[1:])
    weeks = planner_task_weeks(spec)
    assert len(weeks) == 8
    assert weeks[0][0] == date(2025, 12, 29)
    assert weeks[-1][0] == date(2026, 2, 16)


def test_task_seats_stack():
    well = well_rect(NOMAD)
    tasks, notes = task_seats(well, 8)
    assert tasks.y == pytest.approx(well.y)
    assert tasks.h == pytest.approx(checklist_content_height(8))
    assert tasks.w == pytest.approx(well.w)
    assert notes.y == pytest.approx(tasks.bottom + TASK_GAP)
    assert notes.bottom == pytest.approx(well.bottom)
    assert notes.w == pytest.approx(well.w)
    assert notes.h > tasks.h
    assert notes.h > well.h * 0.4


def test_weekly_tasks_paint_template():
    page = WeeklyTasks(
        year=2026,
        iso_week=1,
        monday=date(2025, 12, 29),
        sunday=date(2026, 1, 4),
        tasks=8,
        dest="tasks-2026-W01",
        index_dest="tasks-index-2026",
    )
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_weekly_tasks(plotter, well, page)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("Tasks") == 1
    assert texts.count("Notes") == 1
    assert "This week" not in texts
    assert "Agenda" not in texts
    assert "Action items" not in texts
    assert "Attendees" not in texts
    assert "P" not in texts
    assert "Todo" not in texts
    assert "Doing" not in texts
    assert "Done" not in texts
    assert "Projects" not in texts
    for rejected in ("PROJECT", "Focus", "This month", "Someday"):
        assert rejected not in texts

    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 8

    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []


def test_weekly_tasks_knobs():
    page = WeeklyTasks(
        year=2026,
        iso_week=1,
        monday=date(2025, 12, 29),
        sunday=date(2026, 1, 4),
        tasks=6,
    )
    plotter = RecordingPlotter()
    paint_weekly_tasks(plotter, Rect(4, 20, 110, 90), page)
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 6
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Tasks" in texts
    assert "Notes" in texts


def test_task_header_chip_and_task_tab():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.dest == "tasks-2026-W01")
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Tasks" in texts
    assert "01" in texts
    assert short_date_range(date(2025, 12, 29), date(2026, 1, 4)) in texts
    assert "Projects" not in texts
    assert "Attendees" not in texts
    for label in (
        "Year",
        "Quar",
        "Mon",
        "Habit",
        "Proj",
        "Meet",
        "Task",
        "Week",
        "Day",
        "Notes",
    ):
        assert label in texts
    assert texts.count("Notes") == 2
    assert texts.count("Tasks") >= 2
    chip_links = [op[2] for op in plotter.ops if op[0] == "link" and op[2] == "tasks-index-2026"]
    assert len(chip_links) >= 2
    assert dict(strip_items(page))["Task"] == spec.tasks_index_dest
    assert strip_active(page.kind) == "Task"


def test_tasks_index_focus_seats():
    well = Rect(4, 20, 110, 90)
    focus, listing = tasks_index_focus_seats(well, 7)
    assert focus.x == pytest.approx(well.x)
    assert focus.y == pytest.approx(well.y)
    assert focus.w == pytest.approx(well.w)
    assert listing[0].y > focus.bottom
    assert listing[-1].bottom == pytest.approx(well.bottom)
    assert len(listing) == 7
    leftover = well.h - TASK_INDEX_FOCUS_GAP
    assert focus.h == pytest.approx(
        leftover * TASK_INDEX_FOCUS_WEIGHTS[0] / sum(TASK_INDEX_FOCUS_WEIGHTS)
    )
    band_h = leftover * TASK_INDEX_FOCUS_WEIGHTS[1] / sum(TASK_INDEX_FOCUS_WEIGHTS)
    assert listing[-1].bottom - listing[0].y == pytest.approx(band_h)
    assert focus.h > listing[0].h

    stub, head, ticks = tasks_index_focus_parts(focus)
    assert stub.x > focus.x
    assert head.x == pytest.approx(stub.right)
    assert ticks.y > head.bottom
    assert ticks.bottom < focus.bottom
    assert head.w > stub.w

    row_stub, row_range = tasks_index_list_row(listing[0])
    assert row_stub.x > listing[0].x
    assert row_range.x == pytest.approx(row_stub.right)
    assert row_range.right == pytest.approx(listing[0].right - 1.8)


def test_tasks_index_focus_paint_links():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "tasks_index")
    roster = next(item for item in page.components if isinstance(item, TasksIndex))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_tasks_index_focus(plotter, well, roster)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("This week") == 1
    assert texts.count("Tasks") == 1
    assert short_date_range(date(2025, 12, 29), date(2026, 1, 4)) in texts
    assert short_date_range(date(2026, 1, 5), date(2026, 1, 11)) in texts
    assert "Agenda" not in texts
    assert "Action items" not in texts
    assert "Attendees" not in texts
    assert "P" not in texts
    assert "Todo" not in texts
    assert "Projects" not in texts
    for week in range(1, 9):
        assert f"{week:02d}" in texts

    hero_marks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TASK_INDEX_MARK)
    ]
    assert len(hero_marks) == 1
    list_marks = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[2]
        and not op[3]
        and op[1].w == pytest.approx(TASK_INDEX_LIST_MARK)
    ]
    assert len(list_marks) == 7

    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 3

    links = [op[2] for op in plotter.ops if op[0] == "link"]
    assert links[0] == "tasks-2026-W01"
    assert links[1:] == [f"tasks-2026-W{week:02d}" for week in range(2, 9)]
    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []


def test_tasks_index_header_and_task_active():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "tasks_index")
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Tasks" in texts
    assert "2026" in texts
    assert "Task" in texts
    assert "This week" in texts
    assert "Action items" not in texts
    links = [op[2] for op in plotter.ops if op[0] == "link"]
    assert "tasks-2026-W01" in links
    assert "tasks-2026-W08" in links
    assert spec.tasks_index_dest in links
    assert strip_active(page.kind) == "Task"
    assert dict(strip_items(page))["Task"] == spec.tasks_index_dest


def test_task_index_rows_knob():
    spec = Spec(notes_pages=1, task_index_rows=6)
    pages = YearPlanner().pages(spec)
    roster = next(
        item
        for page in pages
        if page.kind == "tasks_index"
        for item in page.components
        if isinstance(item, TasksIndex)
    )
    assert len(roster.entries) == 6
    dests = [page.dest for page in pages]
    assert "tasks-2026-W07" in dests
    assert "tasks-2026-W08" not in dests
    plotter = RecordingPlotter()
    paint_tasks_index_focus(plotter, Rect(4, 20, 110, 90), roster)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "07" in texts
    assert "08" not in texts
    links = [op[2] for op in plotter.ops if op[0] == "link"]
    assert links[0] == "tasks-2026-W01"
    assert len(links) == 7


def test_task_preview_knob():
    spec = Spec(notes_pages=1, task_preview=2, task_checklist=6)
    pages = YearPlanner().pages(spec)
    roster = next(
        item
        for page in pages
        if page.kind == "tasks_index"
        for item in page.components
        if isinstance(item, TasksIndex)
    )
    assert roster.preview == 2
    leaf = next(item for page in pages if page.kind == "task" for item in page.components if isinstance(item, WeeklyTasks))
    assert leaf.tasks == 6
    plotter = RecordingPlotter()
    paint_tasks_index_focus(plotter, well_rect(NOMAD), roster)
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 2
