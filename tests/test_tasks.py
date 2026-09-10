from datetime import date

import pytest

from parch.books import YearPlanner
from parch.calendar import month_week_bands, short_date_range
from parch.components import TasksIndex, TasksWeekPage
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    RULE,
    RULE_C,
    TASK_GAP,
    TASK_INDEX_BAND_GAP,
    TASK_INDEX_HEAD_H,
    TASK_INDEX_RANGE_W,
    TASK_INDEX_WEEK_W,
    TASK_INDEX_WRITE_GAP,
    TICK,
    checklist_content_height,
    paint_task,
    paint_tasks_index_months,
    strip_active,
    strip_items,
    task_seats,
    tasks_index_band_seats,
    tasks_index_bands,
    tasks_index_link_hits,
    tasks_index_week_parts,
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
    assert page.kind == "task"
    assert page.title == "Tasks"
    dest = next(item for item in page.components if isinstance(item, TasksWeekPage))
    assert dest.year == 2026
    assert dest.iso_year == 2026
    assert dest.iso_week == 1
    assert dest.monday == date(2025, 12, 29)
    assert dest.sunday == date(2026, 1, 4)
    assert dest.rows == 6
    assert dest.index_dest == "tasks-index-2026-Q1"
    assert strip_active(page.kind) == "Task"
    assert strip_items(page) == _TASK_STRIP
    assert ("Task", "tasks-index-2026-Q1") in strip_items(page)
    assert ("Week", "week-2026-W01") in strip_items(page)


def test_tasks_section_order_indexes_then_weeks():
    spec = Spec(notes_pages=1)
    dests = [page.dest for page in TasksSection(spec).pages()]
    assert dests[0] == "tasks-index-2026-Q1"
    assert dests[1:15] == [f"tasks-2026-W{week:02d}" for week in range(1, 15)]
    assert dests[15] == "tasks-index-2026-Q2"
    assert dests.count("tasks-index-2026-Q1") == 1
    assert dests.count("tasks-index-2026-Q4") == 1
    assert [page.kind for page in TasksSection(spec).pages()].count("tasks_index") == 4
    assert [page.kind for page in TasksSection(spec).pages()].count("task") == 53
    week_dests = [dest for dest in dests if dest.startswith("tasks-2026-W")]
    assert week_dests == [f"tasks-2026-W{week:02d}" for week in range(1, 54)]
    assert len(week_dests) == len(set(week_dests))
    july = next(p for p in TasksSection(spec).pages() if p.dest == "tasks-2026-W29")
    well = next(item for item in july.components if isinstance(item, TasksWeekPage))
    assert well.index_dest == "tasks-index-2026-Q3"
    assert dict(strip_items(july))["Task"] == "tasks-index-2026-Q3"
    assert dict(strip_items(july))["Quar"] == "quarter-2026-Q3"


def test_tasks_index_seats_weighted_by_weeks():
    well = well_rect(NOMAD)
    counts = (5, 4, 5)
    bands = tasks_index_bands(well, counts)
    assert len(bands) == 3
    assert bands[0].y == pytest.approx(well.y)
    assert bands[0].x == pytest.approx(well.x)
    assert bands[0].w == pytest.approx(well.w)
    assert bands[-1].bottom == pytest.approx(well.bottom)
    leftover = well.h - TASK_INDEX_BAND_GAP * 2
    assert bands[0].h == pytest.approx(leftover * 5 / 14)
    assert bands[1].h == pytest.approx(leftover * 4 / 14)
    assert bands[2].h == pytest.approx(leftover * 5 / 14)
    assert bands[1].y == pytest.approx(bands[0].bottom + TASK_INDEX_BAND_GAP)

    head, rows = tasks_index_band_seats(bands[0], 5)
    assert head.h == pytest.approx(TASK_INDEX_HEAD_H)
    assert head.x > bands[0].x
    assert len(rows) == 5
    assert rows[0].y > head.bottom
    assert rows[-1].bottom < bands[0].bottom
    stub, dated, write = tasks_index_week_parts(rows[0])
    assert stub.w == pytest.approx(TASK_INDEX_WEEK_W)
    assert dated.x == pytest.approx(stub.right)
    assert dated.w == pytest.approx(TASK_INDEX_RANGE_W)
    assert write.x == pytest.approx(dated.right + TASK_INDEX_WRITE_GAP)
    assert write.right == pytest.approx(rows[0].right)
    assert write.w > dated.w
    assert tasks_index_link_hits(rows[0]) == (stub, dated)
    assert not any(_rects_overlap(hit, write) for hit in tasks_index_link_hits(rows[0]))


def test_task_dest_seats():
    well = well_rect(NOMAD)
    checklist, notes = task_seats(well, 6)
    assert checklist.y == pytest.approx(well.y)
    assert checklist.h == pytest.approx(checklist_content_height(6))
    assert checklist.w == pytest.approx(well.w)
    assert notes.y == pytest.approx(checklist.bottom + TASK_GAP)
    assert notes.bottom == pytest.approx(well.bottom)
    assert notes.h > checklist.h
    assert notes.h > well.h * 0.4


def test_tasks_index_paint_month_headers_and_week_links():
    spec = Spec(notes_pages=1, months=(1, 2, 3))
    page = next(p for p in TasksSection(spec).pages() if p.kind == "tasks_index")
    index = next(item for item in page.components if isinstance(item, TasksIndex))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_tasks_index_months(plotter, well, index)

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
        "Later",
        "Agenda",
        "Attendees",
        "P",
    ):
        assert rejected not in texts

    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert ticks == []

    links = [op[2] for op in plotter.ops if op[0] == "link"]
    assert links == [dest for week in range(1, 15) for dest in (f"tasks-2026-W{week:02d}",) * 2]
    counts = tuple(len(band.weeks) for band in index.bands)
    seats = [
        row
        for band_box, band in zip(tasks_index_bands(well, counts), index.bands, strict=True)
        for row in tasks_index_band_seats(band_box, len(band.weeks))[1]
    ]
    expected_hits: list[tuple[Rect, str]] = []
    for seat, dest in zip(
        seats, [f"tasks-2026-W{week:02d}" for week in range(1, 15)], strict=True
    ):
        stub, dated, write = tasks_index_week_parts(seat)
        hits = tasks_index_link_hits(seat)
        assert hits == (stub, dated)
        assert not any(_rects_overlap(hit, write) for hit in hits)
        expected_hits.extend((hit, dest) for hit in hits)
    assert [(op[1], op[2]) for op in plotter.ops if op[0] == "link"] == expected_hits
    for seat in seats:
        assert all(op[1] != seat for op in plotter.ops if op[0] == "link")

    hlines = [
        op
        for op in plotter.ops
        if op[0] == "line" and op[5] == pytest.approx(RULE) and op[6] == pytest.approx(RULE_C)
    ]
    assert len(hlines) == 14
    for seat, line in zip(seats, hlines, strict=True):
        _stub, _dated, write = tasks_index_week_parts(seat)
        assert line[1] == pytest.approx(write.x)
        assert line[3] == pytest.approx(write.right)
        assert line[2] == pytest.approx(write.bottom)
        assert line[4] == pytest.approx(write.bottom)


def test_task_paint_checklist_and_notes():
    dest = TasksWeekPage(
        year=2026,
        iso_year=2026,
        iso_week=1,
        monday=date(2025, 12, 29),
        sunday=date(2026, 1, 4),
        rows=6,
        index_dest="tasks-index-2026-Q1",
    )
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_task(plotter, well, dest)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("Tasks") == 1
    assert texts.count("Notes") == 1
    assert "Agenda" not in texts
    assert "Action items" not in texts
    assert "Todo" not in texts
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 6


def test_task_header_week_chip_and_task_tab():
    spec = Spec(notes_pages=1, months=(1, 2, 3))
    page = next(p for p in TasksSection(spec).pages() if p.dest == "tasks-2026-W01")
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Tasks" in texts
    assert "W01" in texts
    assert "2026" in texts
    assert "29 Dec–4 Jan" not in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Proj", "Meet", "Task", "Week", "Day", "Notes"):
        assert label in texts
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
    assert "Task" in texts
    assert strip_active(page.kind) == "Task"
    assert dict(strip_items(page))["Task"] == spec.tasks_index_dest


def test_task_rows_knob():
    spec = Spec(notes_pages=1, months=(1,), task_rows=5)
    pages = TasksSection(spec).pages()
    index = next(p for p in pages if p.kind == "tasks_index")
    roster = next(item for item in index.components if isinstance(item, TasksIndex))
    assert roster.quarter == 1
    assert [band.month for band in roster.bands] == [1]
    dests = [page.dest for page in pages]
    assert dests[0] == "tasks-index-2026-Q1"
    assert dests[1:] == [f"tasks-2026-W{week:02d}" for week in range(1, 6)]
    dest = next(item for item in pages[1].components if isinstance(item, TasksWeekPage))
    assert dest.rows == 5
    plotter = RecordingPlotter()
    paint_task(plotter, well_rect(NOMAD), dest)
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 5


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
