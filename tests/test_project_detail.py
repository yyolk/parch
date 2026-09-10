import pytest

from parch.books import YearPlanner
from parch.components import ProjectDetail, ProjectsBoard
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    PROJECT_DEEP_HEADER_H,
    PROJECT_DEEP_META_H,
    PROJECT_DEEP_STATUS_W,
    PROJECT_P,
    PROJECT_STATUS_MARK,
    TICK,
    paint_project_deep,
    project_deep_header_seats,
    project_deep_seats,
    project_deep_tasks_height,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.spec import Spec


def test_project_detail_page_after_board():
    spec = Spec(notes_pages=1)
    pages = YearPlanner().pages(spec)
    assert pages[2].kind == "projects"
    page = pages[3]
    assert page.dest == "project-detail-2026"
    assert page.kind == "project_detail"
    assert page.title == "Project"
    assert pages[4].dest == "quarter-2026-Q1"

    board = next(item for item in pages[2].components if isinstance(item, ProjectsBoard))
    assert board.cards == 3
    assert board.tasks == 4

    detail = next(item for item in page.components if isinstance(item, ProjectDetail))
    assert detail.year == 2026
    assert detail.tasks == 9

    assert strip_active(page.kind) == ""
    assert strip_items(page) == (
        ("Year", "year-2026"),
        ("Quar", "quarter-2026-Q1"),
        ("Mon", "month-2026-01"),
        ("Habit", "month-2026-01-habits"),
        ("Week", "week-2026-W01"),
        ("Day", "2026-01-01"),
        ("Notes", "2026-01-01-notes-1"),
    )


def test_project_deep_seat_split():
    well = well_rect(NOMAD)
    header, meta, tasks, notes = project_deep_seats(well, 9)
    assert header.y == pytest.approx(well.y)
    assert header.x == pytest.approx(well.x)
    assert header.w == pytest.approx(well.w)
    assert header.h == pytest.approx(PROJECT_DEEP_HEADER_H)
    assert meta.y > header.bottom
    assert meta.h == pytest.approx(PROJECT_DEEP_META_H)
    assert tasks.y > meta.bottom
    assert tasks.h == pytest.approx(project_deep_tasks_height(9))
    assert notes.y > tasks.bottom
    assert notes.bottom == pytest.approx(well.bottom)
    assert notes.h > well.h / 2
    assert notes.h > tasks.h
    assert notes.h > header.h + meta.h + tasks.h

    name, status = project_deep_header_seats(header)
    assert name.x == pytest.approx(header.x)
    assert status.right == pytest.approx(header.right)
    assert name.right < status.x
    assert status.w == pytest.approx(PROJECT_DEEP_STATUS_W)


def test_project_deep_paint_one_project():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "project_detail")
    detail = next(item for item in page.components if isinstance(item, ProjectDetail))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_project_deep(plotter, well, detail)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("P") == 1
    assert texts.count("Todo") == 1
    assert texts.count("Doing") == 1
    assert texts.count("Done") == 1
    assert texts.count("#") == 1
    assert "PROJECT" not in texts
    assert "Focus" not in texts
    assert "Notes" not in texts
    assert "TO DO" not in texts
    assert "IN PROGRESS" not in texts

    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 9

    marks = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[2]
        and not op[3]
        and op[1].w == pytest.approx(PROJECT_STATUS_MARK)
    ]
    assert len(marks) == 3

    p_boxes = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(PROJECT_P)
    ]
    assert len(p_boxes) == 1

    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []

    lines = [op for op in plotter.ops if op[0] == "line"]
    assert all(op[2] == op[4] for op in lines), "notes and rules stay orthogonal — no diagonal status"


def test_project_deep_tasks_knob():
    spec = Spec(notes_pages=1, project_detail_tasks=10)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "project_detail")
    detail = next(item for item in page.components if isinstance(item, ProjectDetail))
    assert detail.tasks == 10
    plotter = RecordingPlotter()
    paint_project_deep(plotter, Rect(4, 20, 110, 120), detail)
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 10


def test_project_detail_header_year_and_seven_tabs():
    spec = Spec(notes_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "project_detail")
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Project" in texts
    assert "Projects" not in texts
    assert "2026" in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Week", "Day", "Notes"):
        assert label in texts
