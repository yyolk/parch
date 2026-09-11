"""Strangler allowlist. Listed painters must not emit face-only text."""

from pathlib import Path

import pytest

from parch.books import YearPlanner
from parch.components import (
    AnnualGrid,
    AnnualMonth,
    CoverTitle,
    HabitGrid,
    MeetingAgenda,
    MeetingIndex,
    MonthGrid,
    Notes,
    Priorities,
    ProjectsBoard,
    ProjectsIndex,
    QuarterGrid,
    ReviewIndex,
    ReviewWeekPage,
    Schedule,
    TasksIndex,
    TasksWeekPage,
    WeekStrip,
)
from parch.devices.nomad import NOMAD
from parch.fonts import MIGRATED_SURFACES, JostRamp, MigratedSurface
from parch.geom import Rect
from parch.layouts.planner import painters as planner_painters
from parch.layouts.planner.painters import (
    paint_annual,
    paint_cover,
    paint_daily,
    paint_habit_grid,
    paint_header,
    paint_meeting,
    paint_meetings_index,
    paint_month_grid,
    paint_nav,
    paint_notes,
    paint_priorities,
    paint_project,
    paint_projects_index,
    paint_quarter,
    paint_review,
    paint_review_index,
    paint_schedule,
    paint_task,
    paint_tasks_index,
    paint_week,
    well_rect,
)
from parch.plotter import RecordingPlotter
from parch.spec import Spec


def _pages():
    return YearPlanner().pages(Spec(notes_pages=1))


def _one(page, typ):
    for item in page.components:
        if isinstance(item, typ):
            return item
    raise TypeError(f"{page.kind} missing {typ.__name__}")


def _page(dest: str):
    return next(page for page in _pages() if page.dest == dest)


def test_allowlist_is_closed_and_real():
    assert MIGRATED_SURFACES == frozenset(MigratedSurface)
    assert {s.value for s in MIGRATED_SURFACES} == {
        "paint_cover",
        "paint_header",
        "paint_nav",
        "paint_annual",
        "paint_month_grid",
        "paint_week",
        "paint_daily",
        "paint_notes",
        "paint_schedule",
        "paint_priorities",
        "paint_projects_index",
        "paint_project",
        "paint_quarter",
        "paint_habit_grid",
        "paint_meetings_index",
        "paint_meeting",
        "paint_review_index",
        "paint_review",
        "paint_tasks_index",
        "paint_task",
    }
    for name in MIGRATED_SURFACES:
        assert callable(getattr(planner_painters, name))


def test_painters_source_has_no_face_or_bold_kwargs():
    src = Path("src/parch/layouts/planner/painters.py").read_text(encoding="utf-8")
    assert "face=" not in src
    assert "bold=" not in src


def _assert_inked(plotter: RecordingPlotter) -> None:
    assert plotter.text_ops()
    assert plotter.face_only_text() == []


def test_listed_painters_do_not_emit_face_only_text():
    ramp = JostRamp()
    well = well_rect(NOMAD)
    pages = _pages()

    cover = next(page for page in pages if page.kind == "cover")
    ink = RecordingPlotter()
    paint_cover(ink, NOMAD, _one(cover, CoverTitle), ramp=ramp)
    _assert_inked(ink)

    ink = RecordingPlotter()
    paint_header(ink, NOMAD, "Year", "2026", chip="01", ramp=ramp)
    _assert_inked(ink)

    ink = RecordingPlotter()
    paint_nav(ink, NOMAD, (("Year", "year-2026"), ("Mon", "month-2026-01")), "Year", ramp=ramp)
    _assert_inked(ink)

    annual = next(page for page in pages if page.kind == "annual")
    ink = RecordingPlotter()
    paint_annual(ink, well, _one(annual, AnnualGrid), ramp=ramp)
    _assert_inked(ink)

    month = _page("month-2026-01")
    ink = RecordingPlotter()
    paint_month_grid(ink, well, _one(month, MonthGrid), ramp=ramp)
    _assert_inked(ink)

    week = _page("week-2026-W01")
    ink = RecordingPlotter()
    paint_week(ink, well, _one(week, WeekStrip), ramp=ramp)
    _assert_inked(ink)

    daily = _page("2026-01-15")
    ink = RecordingPlotter()
    paint_daily(
        ink,
        well,
        _one(daily, Schedule),
        _one(daily, AnnualMonth),
        _one(daily, Priorities),
        _one(daily, Notes),
        ramp=ramp,
    )
    _assert_inked(ink)

    ink = RecordingPlotter()
    paint_schedule(ink, well, _one(daily, Schedule), ramp=ramp)
    _assert_inked(ink)

    ink = RecordingPlotter()
    paint_priorities(ink, well, _one(daily, Priorities), ramp=ramp)
    _assert_inked(ink)

    notes = next(page for page in pages if page.kind == "daily_notes")
    ink = RecordingPlotter()
    paint_notes(ink, well, _one(notes, Notes), ramp=ramp)
    _assert_inked(ink)

    projects = next(page for page in pages if page.kind == "projects_index")
    ink = RecordingPlotter()
    paint_projects_index(ink, well, _one(projects, ProjectsIndex), ramp=ramp)
    _assert_inked(ink)

    project = next(page for page in pages if page.kind == "project")
    ink = RecordingPlotter()
    paint_project(ink, well, _one(project, ProjectsBoard), ramp=ramp)
    _assert_inked(ink)

    quarter = next(page for page in pages if page.kind == "quarter")
    grid = _one(quarter, QuarterGrid)
    ink = RecordingPlotter()
    paint_quarter(ink, well, grid, ramp=ramp)
    _assert_inked(ink)

    habit = _page("month-2026-01-habits")
    habit_grid = _one(habit, HabitGrid)
    ink = RecordingPlotter()
    paint_habit_grid(ink, well, habit_grid, ramp=ramp)
    _assert_inked(ink)

    ink = RecordingPlotter()
    paint_meetings_index(ink, well, _one(_page("meetings-index-2026"), MeetingIndex), ramp=ramp)
    _assert_inked(ink)

    ink = RecordingPlotter()
    paint_meeting(ink, well, _one(_page("meeting-2026-01"), MeetingAgenda), ramp=ramp)
    _assert_inked(ink)

    ink = RecordingPlotter()
    paint_review_index(ink, well, _one(_page("review-index-2026"), ReviewIndex), ramp=ramp)
    _assert_inked(ink)

    ink = RecordingPlotter()
    paint_review(ink, well, _one(_page("review-2026-W01"), ReviewWeekPage), ramp=ramp)
    _assert_inked(ink)

    ink = RecordingPlotter()
    paint_tasks_index(ink, well, _one(_page("tasks-index-2026-Q1"), TasksIndex), ramp=ramp)
    _assert_inked(ink)

    ink = RecordingPlotter()
    paint_task(ink, well, _one(_page("tasks-2026-W01"), TasksWeekPage), ramp=ramp)
    _assert_inked(ink)


def test_text_requires_ink_or_ref():
    ink = RecordingPlotter()
    with pytest.raises(TypeError, match="ink= or ref="):
        ink.text(Rect(0, 0, 10, 4), "leak")
