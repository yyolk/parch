from datetime import date

import pytest

from parch.books import YearPlanner
from parch.calendar import month_week_bands, short_date_range
from parch.components import TasksIndex, WeeklyTasks
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    TASK_COL_GAP,
    TASK_GAP,
    TASK_INDEX_BAND_GAP,
    TASK_INDEX_CHIP_GAP,
    TASK_INDEX_CHIP_W,
    TASK_INDEX_COL_GAP,
    TASK_INDEX_HEAD_H,
    TICK,
    checklist_content_height,
    paint_tasks_index_bands,
    paint_weekly_tasks,
    strip_active,
    strip_items,
    task_index_chip_parts,
    task_index_link_hits,
    tasks_index_band_seats,
    tasks_index_bands,
    tasks_index_chip_rows,
    weekly_tasks_seats,
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
    ("Task", "tasks-index-2026-Q1"),
    ("Week", "week-2026-W01"),
    ("Day", "2026-01-01"),
    ("Notes", "2026-01-01-notes-1"),
)


def test_tasks_not_in_year_planner():
    spec = Spec(notes_pages=1)
    dests = [page.dest for page in YearPlanner().pages(spec)]
    assert dests[12] == "meetings-index-2026"
    assert dests[29] == "quarter-2026-Q1"
    assert not any(dest.startswith("tasks-") for dest in dests)
    year = next(page for page in YearPlanner().pages(spec) if page.kind == "annual")
    labels = [label for label, _ in strip_items(year)]
    assert "Task" not in labels
    assert labels == ["Year", "Quar", "Mon", "Habit", "Proj", "Meet", "Week", "Day", "Notes"]


def test_tasks_index_page():
    spec = Spec(notes_pages=1, months=(1, 2, 3))
    page = next(p for p in TasksSection(spec).pages() if p.kind == "tasks_index")
    assert page.dest == "tasks-index-2026-Q1"
    assert page.title == "Tasks"
    index = next(item for item in page.components if isinstance(item, TasksIndex))
    assert index.year == 2026
    assert index.quarter == 1
    assert index.dest == "tasks-index-2026-Q1"
    assert [band.month for band in index.bands] == [1, 2, 3]
    assert [band.name for band in index.bands] == ["January", "February", "March"]
    assert [len(band.weeks) for band in index.bands] == [5, 4, 5]
    assert index.bands[0].weeks[0].dest == "tasks-2026-W01"
    assert index.bands[0].weeks[-1].iso_week == 5
    assert index.bands[1].weeks[0].iso_week == 6
    assert index.bands[2].weeks[-1].iso_week == 14
    assert strip_active(page.kind) == "Task"
    assert strip_items(page) == _TASK_STRIP


def test_tasks_dest_page():
    spec = Spec(notes_pages=1, months=(1, 2, 3))
    page = next(p for p in TasksSection(spec).pages() if p.dest == "tasks-2026-W01")
    assert page.kind == "tasks"
    assert page.title == "Tasks"
    dest = next(item for item in page.components if isinstance(item, WeeklyTasks))
    assert dest.year == 2026
    assert dest.iso_year == 2026
    assert dest.iso_week == 1
    assert dest.monday == date(2025, 12, 29)
    assert dest.sunday == date(2026, 1, 4)
    assert dest.morning == 6
    assert dest.later == 6
    assert dest.index_dest == "tasks-index-2026-Q1"
    assert strip_active(page.kind) == "Task"
    assert strip_items(page) == _TASK_STRIP
    assert ("Task", "tasks-index-2026-Q1") in strip_items(page)
    assert ("Week", "week-2026-W01") in strip_items(page)
    assert ("Day", "2026-01-01") in strip_items(page)


def test_tasks_section_order_indexes_then_weeks():
    spec = Spec(notes_pages=1)
    dests = [page.dest for page in TasksSection(spec).pages()]
    assert dests[0] == "tasks-index-2026-Q1"
    assert dests[1:15] == [f"tasks-2026-W{week:02d}" for week in range(1, 15)]
    assert dests[15] == "tasks-index-2026-Q2"
    assert dests.count("tasks-index-2026-Q1") == 1
    assert dests.count("tasks-index-2026-Q4") == 1
    assert [page.kind for page in TasksSection(spec).pages()].count("tasks_index") == 4
    assert [page.kind for page in TasksSection(spec).pages()].count("tasks") == 53
    week_dests = [dest for dest in dests if dest.startswith("tasks-2026-W")]
    assert week_dests == [f"tasks-2026-W{week:02d}" for week in range(1, 54)]
    assert len(week_dests) == len(set(week_dests))
    july = next(p for p in TasksSection(spec).pages() if p.dest == "tasks-2026-W29")
    well = next(item for item in july.components if isinstance(item, WeeklyTasks))
    assert well.index_dest == "tasks-index-2026-Q3"
    assert dict(strip_items(july))["Task"] == "tasks-index-2026-Q3"
    assert dict(strip_items(july))["Quar"] == "quarter-2026-Q3"


def test_tasks_index_seats_weighted_by_chip_rows():
    well = well_rect(NOMAD)
    counts = (5, 4, 5)
    bands = tasks_index_bands(well, counts)
    assert len(bands) == 3
    assert bands[0].y == pytest.approx(well.y)
    assert bands[0].x == pytest.approx(well.x)
    assert bands[0].w == pytest.approx(well.w)
    assert bands[-1].bottom == pytest.approx(well.bottom)
    leftover = well.h - TASK_INDEX_BAND_GAP * 2
    assert tasks_index_chip_rows(5) == 3
    assert tasks_index_chip_rows(4) == 2
    assert bands[0].h == pytest.approx(leftover * 3 / 8)
    assert bands[1].h == pytest.approx(leftover * 2 / 8)
    assert bands[2].h == pytest.approx(leftover * 3 / 8)
    assert bands[1].y == pytest.approx(bands[0].bottom + TASK_INDEX_BAND_GAP)

    head, chips = tasks_index_band_seats(bands[0], 5)
    assert head.h == pytest.approx(TASK_INDEX_HEAD_H)
    assert head.x > bands[0].x
    assert len(chips) == 5
    assert chips[0].y > head.bottom
    assert chips[-1].bottom < bands[0].bottom
    assert chips[1].x > chips[0].right
    assert chips[1].y == pytest.approx(chips[0].y)
    assert chips[2].x == pytest.approx(chips[0].x)
    assert chips[2].y > chips[0].bottom
    chip, labeled = task_index_chip_parts(chips[0])
    assert chip.w == pytest.approx(TASK_INDEX_CHIP_W)
    assert labeled.x == pytest.approx(chip.right + TASK_INDEX_CHIP_GAP)
    hits = task_index_link_hits(chips[0])
    assert hits == (chip,)
    assert not _rects_overlap(hits[0], labeled)
    assert chips[1].x == pytest.approx(chips[0].right + TASK_INDEX_COL_GAP)


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


def test_tasks_index_paint_month_headers_and_week_chips():
    spec = Spec(notes_pages=1, months=(1, 2, 3))
    page = next(p for p in TasksSection(spec).pages() if p.kind == "tasks_index")
    index = next(item for item in page.components if isinstance(item, TasksIndex))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_tasks_index_bands(plotter, well, index)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "January" in texts
    assert "February" in texts
    assert "March" in texts
    for week in range(1, 15):
        assert f"W{week:02d}" in texts
    assert "29 Dec–4 Jan" in texts
    assert short_date_range(date(2026, 1, 26), date(2026, 2, 1)) in texts
    for rejected in (
        "Todo",
        "Doing",
        "Done",
        "Active",
        "Waiting",
        "This week",
        "Next week",
        "Morning",
        "Agenda",
        "Attendees",
        "P",
    ):
        assert rejected not in texts

    chips = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TASK_INDEX_CHIP_W)
    ]
    assert len(chips) == 14

    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert ticks == []

    counts = tuple(len(band.weeks) for band in index.bands)
    seats = [
        cell
        for band_box, band in zip(tasks_index_bands(well, counts), index.bands, strict=True)
        for cell in tasks_index_band_seats(band_box, len(band.weeks))[1]
    ]
    weeks = [week for band in index.bands for week in band.weeks]
    link_ops = [op for op in plotter.ops if op[0] == "link"]
    expected = [(task_index_link_hits(seat)[0], week.dest) for seat, week in zip(seats, weeks, strict=True)]
    assert [(op[1], op[2]) for op in link_ops] == expected
    assert [dest for _, dest in expected] == [f"tasks-2026-W{week:02d}" for week in range(1, 15)]


def test_weekly_tasks_paint_template():
    dest = WeeklyTasks(
        year=2026,
        iso_year=2026,
        iso_week=1,
        monday=date(2025, 12, 29),
        sunday=date(2026, 1, 4),
        morning=6,
        later=6,
        index_dest="tasks-index-2026-Q1",
    )
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_weekly_tasks(plotter, well, dest)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("Morning") == 1
    assert texts.count("Later") == 1
    assert texts.count("Notes") == 1
    assert "Focus" not in texts
    assert "Agenda" not in texts
    assert "Action items" not in texts
    assert "Todo" not in texts
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 6 + 6
    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []


def test_weekly_tasks_knobs():
    dest = WeeklyTasks(
        year=2026,
        iso_year=2026,
        iso_week=2,
        monday=date(2026, 1, 5),
        sunday=date(2026, 1, 11),
        morning=4,
        later=5,
        index_dest="tasks-index-2026-Q1",
    )
    plotter = RecordingPlotter()
    paint_weekly_tasks(plotter, Rect(4, 20, 110, 90), dest)
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


def test_task_header_week_chip_and_task_tab():
    spec = Spec(notes_pages=1, months=(1, 2, 3))
    page = next(p for p in TasksSection(spec).pages() if p.dest == "tasks-2026-W01")
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Tasks" in texts
    assert "W01" in texts
    assert "Morning" in texts
    assert "Later" in texts
    assert short_date_range(date(2025, 12, 29), date(2026, 1, 4)) in texts
    assert "Focus" not in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Proj", "Meet", "Task", "Week", "Day", "Notes"):
        assert label in texts
    assert texts.count("Notes") == 2
    assert strip_active(page.kind) == "Task"
    links = [op[2] for op in plotter.ops if op[0] == "link"]
    assert links.count("tasks-index-2026-Q1") >= 2
    chip = next(op[1] for op in plotter.ops if op[0] == "text" and op[2] == "W01")
    assert any(
        op[0] == "link" and op[2] == "tasks-index-2026-Q1" and _rects_overlap(op[1], chip)
        for op in plotter.ops
    )


def test_tasks_index_chrome_task_tab():
    spec = Spec(notes_pages=1, months=(1, 2, 3))
    page = next(p for p in TasksSection(spec).pages() if p.kind == "tasks_index")
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Tasks" in texts
    assert "Q1" in texts
    assert "January" in texts
    assert "W01" in texts
    assert "Task" in texts
    assert strip_active(page.kind) == "Task"
    assert dict(strip_items(page))["Task"] == spec.tasks_index_dest


def test_task_morning_later_knobs():
    spec = Spec(notes_pages=1, months=(1,), task_morning=5, task_later=4)
    pages = TasksSection(spec).pages()
    index = next(p for p in pages if p.kind == "tasks_index")
    roster = next(item for item in index.components if isinstance(item, TasksIndex))
    assert roster.quarter == 1
    assert [band.month for band in roster.bands] == [1]
    dests = [page.dest for page in pages]
    assert dests[0] == "tasks-index-2026-Q1"
    assert dests[1:] == [f"tasks-2026-W{week:02d}" for week in range(1, 6)]
    dest = next(item for item in pages[1].components if isinstance(item, WeeklyTasks))
    assert dest.morning == 5
    assert dest.later == 4
    plotter = RecordingPlotter()
    paint_weekly_tasks(plotter, well_rect(NOMAD), dest)
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 5 + 4


def test_q1_bands_match_calendar():
    spec = Spec(months=(1, 2, 3))
    index = next(
        item
        for page in TasksSection(spec).pages()
        if page.kind == "tasks_index"
        for item in page.components
        if isinstance(item, TasksIndex)
    )
    calendar = month_week_bands(2026, (1, 2, 3), weekday_start=0)
    assert [len(band.weeks) for band in index.bands] == [len(weeks) for _month, weeks in calendar]
    assert index.bands[0].weeks[0].monday == calendar[0][1][0][0]
