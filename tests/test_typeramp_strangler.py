"""Strangler allowlist. Listed painters must not emit face-only text."""

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
    ProjectsIndex,
    ReviewIndex,
    ReviewWeekPage,
    Schedule,
    TasksIndex,
    WeekStrip,
)
from parch.devices.nomad import NOMAD
from parch.fonts import BRIDGE_BACKLOG, MIGRATED_SURFACES, JostRamp, MigratedSurface
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
    paint_projects_index,
    paint_review,
    paint_review_index,
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
        "paint_projects_index",
    }
    assert MIGRATED_SURFACES.isdisjoint(BRIDGE_BACKLOG)
    for name in (*MIGRATED_SURFACES, *BRIDGE_BACKLOG):
        assert callable(getattr(planner_painters, name))


def test_listed_painters_do_not_emit_face_only_text():
    ramp = JostRamp()
    well = well_rect(NOMAD)
    pages = _pages()

    cover = next(page for page in pages if page.kind == "cover")
    ink = RecordingPlotter()
    paint_cover(ink, NOMAD, _one(cover, CoverTitle), ramp=ramp)
    assert ink.face_only_text() == []

    ink = RecordingPlotter()
    paint_header(ink, NOMAD, "Year", "2026", chip="01", ramp=ramp)
    assert ink.face_only_text() == []

    ink = RecordingPlotter()
    paint_nav(ink, NOMAD, (("Year", "year-2026"), ("Mon", "month-2026-01")), "Year", ramp=ramp)
    assert ink.text_ops()
    assert ink.face_only_text() == []

    annual = next(page for page in pages if page.kind == "annual")
    ink = RecordingPlotter()
    paint_annual(ink, well, _one(annual, AnnualGrid), ramp=ramp)
    assert ink.text_ops()
    assert ink.face_only_text() == []

    month = _page("month-2026-01")
    ink = RecordingPlotter()
    paint_month_grid(ink, well, _one(month, MonthGrid), ramp=ramp)
    assert ink.text_ops()
    assert ink.face_only_text() == []

    week = _page("week-2026-W01")
    ink = RecordingPlotter()
    paint_week(ink, well, _one(week, WeekStrip), ramp=ramp)
    assert ink.text_ops()
    assert ink.face_only_text() == []

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
    assert ink.text_ops()
    assert ink.face_only_text() == []

    projects = next(page for page in pages if page.kind == "projects_index")
    ink = RecordingPlotter()
    paint_projects_index(ink, well, _one(projects, ProjectsIndex), ramp=ramp)
    assert ink.text_ops()
    assert ink.face_only_text() == []


@pytest.mark.parametrize(
    ("dest", "painter", "typ"),
    [
        ("month-2026-01-habits", paint_habit_grid, HabitGrid),
        ("meetings-index-2026", paint_meetings_index, MeetingIndex),
        ("meeting-2026-01", paint_meeting, MeetingAgenda),
        ("review-index-2026", paint_review_index, ReviewIndex),
        ("review-2026-W01", paint_review, ReviewWeekPage),
        ("tasks-index-2026-Q1", paint_tasks_index, TasksIndex),
    ],
)
def test_bridge_backlog_still_emits_face_only(dest, painter, typ):
    page = _page(dest)
    ink = RecordingPlotter()
    painter(ink, well_rect(NOMAD), _one(page, typ))
    leftover = ink.face_only_text()
    assert leftover, f"{painter.__name__} should still emit face-only FaceBridge ops"
    assert all(op[10] is None for op in leftover)


def test_task_dest_stays_off_allowlist():
    """Weekly Tasks dest is backlog: not listed, even if shared notes use a step helper."""
    assert "paint_task" in BRIDGE_BACKLOG
    assert MigratedSurface.DAILY.value != "paint_task"
    assert "paint_task" not in {s.value for s in MIGRATED_SURFACES}


def test_listed_painter_regression_detects_face_only():
    """RecordingPlotter.face_only_text is what CI uses to catch a half-migrated listed painter."""
    ink = RecordingPlotter()
    from parch.geom import Rect

    ink.text(Rect(0, 0, 10, 4), "leak", face="sans", size=6.4)
    leaked = ink.face_only_text()
    assert len(leaked) == 1
    assert leaked[0][2] == "leak"
    assert leaked[0][10] is None
