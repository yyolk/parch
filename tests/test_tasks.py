import pytest

from parch.books import YearPlanner
from parch.components import TasksIndex, WeeklyTasks
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    TASK_COVER_GAP,
    TASK_COVER_INSET_X,
    TASK_COVER_INSET_Y,
    TASK_COVER_LABEL_H,
    TASK_COVER_TICKS,
    TASK_GAP,
    TICK,
    checklist_content_height,
    paint_tasks_index_covers,
    paint_weekly_tasks,
    strip_active,
    strip_items,
    task_cover_cols,
    task_cover_label,
    tasks_index_covers,
    weekly_tasks_seats,
)
from parch.plotter import RecordingPlotter
from parch.sections.tasks import TASK_ROWS, TasksSection
from parch.spec import Spec


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
    assert dests[12] == "meetings-index-2026"
    assert dests[13:29] == [f"meeting-2026-{slot:02d}" for slot in range(1, 17)]
    assert dests[29] == "tasks-index-2026-01"
    assert dests[30:42] == [f"tasks-2026-{slot:02d}" for slot in range(1, 13)]
    assert dests[42] == "quarter-2026-Q1"
    assert [page.kind for page in pages].count("tasks_index") == 1
    assert [page.kind for page in pages].count("weekly_tasks") == 12


def test_tasks_index_page():
    spec = Spec(notes_pages=1)
    page = next(p for p in TasksSection(spec).pages() if p.kind == "tasks_index")
    assert page.dest == "tasks-index-2026-01"
    assert page.title == "Tasks"
    roster = next(item for item in page.components if isinstance(item, TasksIndex))
    assert roster.year == 2026
    assert roster.dest == "tasks-index-2026-01"
    assert len(roster.covers) == 12
    assert [cover.number for cover in roster.covers] == list(range(1, 13))
    assert [cover.dest for cover in roster.covers] == [
        f"tasks-2026-{slot:02d}" for slot in range(1, 13)
    ]
    assert strip_active(page.kind) == "Task"
    assert strip_items(page) == _TASK_STRIP


def test_weekly_tasks_dest_page():
    spec = Spec(notes_pages=1)
    page = next(p for p in TasksSection(spec).pages() if p.dest == "tasks-2026-03")
    assert page.kind == "weekly_tasks"
    assert page.title == "Tasks"
    well = next(item for item in page.components if isinstance(item, WeeklyTasks))
    assert well.year == 2026
    assert well.rows == TASK_ROWS == 7
    assert well.number == 3
    assert well.index_dest == "tasks-index-2026-01"
    assert strip_active(page.kind) == "Task"
    assert strip_items(page) == _TASK_STRIP
    assert ("Task", "tasks-index-2026-01") in strip_items(page)


def test_weekly_tasks_seats_stack():
    well = well_rect(NOMAD)
    checklist, notes = weekly_tasks_seats(well, 7)
    assert checklist.y == pytest.approx(well.y)
    assert checklist.h == pytest.approx(checklist_content_height(7))
    assert checklist.x == pytest.approx(well.x)
    assert checklist.w == pytest.approx(well.w)
    assert notes.y == pytest.approx(checklist.bottom + TASK_GAP)
    assert notes.bottom == pytest.approx(well.bottom)
    assert notes.w == pytest.approx(well.w)
    assert notes.h > checklist.h
    assert notes.h > well.h * 0.4


def test_weekly_tasks_paint_template():
    tasks = WeeklyTasks(year=2026, rows=7, index_dest="tasks-index-2026-01", number=1)
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_weekly_tasks(plotter, well, tasks)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("Tasks") == 1
    assert texts.count("Notes") == 1
    assert "Agenda" not in texts
    assert "Action items" not in texts
    assert "Title" not in texts
    assert "Date" not in texts
    assert "Attendees" not in texts
    assert "P" not in texts
    assert "Todo" not in texts
    assert "Doing" not in texts
    assert "Done" not in texts
    assert "Projects" not in texts
    for rejected in ("Focus", "This week", "This month", "Someday", "Priorities"):
        assert rejected not in texts

    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 7
    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []


def test_weekly_tasks_header_year_chip_and_task_tab():
    spec = Spec(notes_pages=1)
    page = next(p for p in TasksSection(spec).pages() if p.dest == "tasks-2026-01")
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Tasks" in texts
    assert "2026" in texts
    assert "W01" in texts
    assert "Projects" not in texts
    assert "Agenda" not in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Proj", "Meet", "Task", "Week", "Day", "Notes"):
        assert label in texts
    assert texts.count("Notes") == 2
    assert strip_active(page.kind) == "Task"
    links = [op[2] for op in plotter.ops if op[0] == "link"]
    assert links.count("tasks-index-2026-01") >= 2


def test_task_cover_grid_seats():
    well = well_rect(NOMAD)
    seats = tasks_index_covers(well, 12)
    assert len(seats) == 12
    assert task_cover_cols(12) == 3
    assert task_cover_cols(6) == 2
    assert seats[0].x == pytest.approx(well.x)
    assert seats[0].y == pytest.approx(well.y)
    assert seats[1].x > seats[0].right
    assert seats[1].y == pytest.approx(seats[0].y)
    assert seats[2].x > seats[1].right
    assert seats[3].y > seats[0].bottom
    assert seats[3].x == pytest.approx(seats[0].x)
    assert seats[11].bottom == pytest.approx(well.bottom)
    assert seats[2].right == pytest.approx(well.right)
    leftover_w = well.w - TASK_COVER_GAP * 2
    assert seats[0].w == pytest.approx(leftover_w / 3)
    leftover_h = well.h - TASK_COVER_GAP * 3
    assert seats[0].h == pytest.approx(leftover_h / 4)
    assert seats[1].x - seats[0].right == pytest.approx(TASK_COVER_GAP)
    assert seats[3].y - seats[0].bottom == pytest.approx(TASK_COVER_GAP)

    six = tasks_index_covers(well, 6)
    assert len(six) == 6
    assert task_cover_cols(6) == 2
    assert six[1].x > six[0].right
    assert six[2].y > six[0].bottom
    assert six[2].x == pytest.approx(six[0].x)
    assert six[5].bottom == pytest.approx(well.bottom)

    label = task_cover_label(seats[0])
    assert label.x == pytest.approx(seats[0].x + TASK_COVER_INSET_X)
    assert label.y == pytest.approx(seats[0].y + TASK_COVER_INSET_Y)
    assert label.h == pytest.approx(TASK_COVER_LABEL_H)


def test_tasks_index_paint_covers_and_links():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "tasks_index")
    roster = next(item for item in page.components if isinstance(item, TasksIndex))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_tasks_index_covers(plotter, well, roster)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    for slot in range(1, 13):
        assert f"W{slot:02d}" in texts
    assert "Tasks" not in texts
    assert "Notes" not in texts
    assert "Agenda" not in texts
    assert "Title" not in texts
    assert "P" not in texts
    assert "Todo" not in texts

    seats = tasks_index_covers(well, 12)
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

    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 12 * TASK_COVER_TICKS

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
    assert "Tasks" in chrome_texts
    assert "Task" in chrome_texts
    assert "2026" in chrome_texts
    assert "Agenda" not in chrome_texts
    assert strip_active(page.kind) == "Task"
    assert dict(strip_items(page))["Task"] == spec.tasks_index_dest


def test_task_covers_and_pages_knobs():
    spec = Spec(notes_pages=1, task_covers=6, task_index_pages=2)
    assert spec.task_count == 12
    pages = TasksSection(spec).pages()
    indexes = [page for page in pages if page.kind == "tasks_index"]
    assert len(indexes) == 2
    dests = [page.dest for page in pages]
    assert dests[0:2] == ["tasks-index-2026-01", "tasks-index-2026-02"]
    assert dests[2:] == [f"tasks-2026-{slot:02d}" for slot in range(1, 13)]
    page_one = next(item for item in indexes[0].components if isinstance(item, TasksIndex))
    page_two = next(item for item in indexes[1].components if isinstance(item, TasksIndex))
    assert [cover.number for cover in page_one.covers] == list(range(1, 7))
    assert [cover.number for cover in page_two.covers] == list(range(7, 13))
    assert task_cover_cols(6) == 2
    plotter = RecordingPlotter()
    paint_tasks_index_covers(plotter, well_rect(NOMAD), page_two)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "W07" in texts
    assert "W12" in texts
    assert "W01" not in texts
    assert [op[2] for op in plotter.ops if op[0] == "link"] == [
        f"tasks-2026-{slot:02d}" for slot in range(7, 13)
    ]
    leaf = next(page for page in pages if page.dest == "tasks-2026-10")
    well = next(item for item in leaf.components if isinstance(item, WeeklyTasks))
    assert well.number == 10
    assert well.index_dest == "tasks-index-2026-02"
    assert dict(strip_items(leaf))["Task"] == "tasks-index-2026-02"
    chrome = RecordingPlotter()
    chrome.begin_page()
    PlannerLayout().paint(leaf, chrome, NOMAD)
    labels = [op[2] for op in chrome.ops if op[0] == "text"]
    assert "W10" in labels
    assert "tasks-index-2026-02" in [op[2] for op in chrome.ops if op[0] == "link"]
    assert "tasks-index-2026-01" not in [op[2] for op in chrome.ops if op[0] == "link"]
