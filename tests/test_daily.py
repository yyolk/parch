from datetime import date, time

import pytest
from tomlrange import Clock

from parch.books import YearPlanner
from parch.components import AnnualMonth, Notes, Priorities, Schedule
from parch.devices.registry import NOMAD
from parch.geom import Rect
from parch.layouts.planner.layout import (
    COL_GAP,
    DAILY_COL_WEIGHTS,
    DAILY_MINI_GAP,
    DAILY_MINI_H,
    DAILY_PRIO_GAP,
    daily_left_seats,
    daily_right_seats,
    well_rect,
)
from parch.layouts.planner.painters import (
    TICK,
    WASH,
    _paint_mini_month,
    checklist_content_height,
    paint_priorities,
    paint_schedule,
)
from parch.plotter import RecordingPlotter
from parch.sections.daily import DailySection
from parch.spec import Spec
from parch.tracks import columns


def test_daily_has_mini_month_daily_notes_does_not():
    spec = Spec(notes_pages=1)
    pages = YearPlanner().pages(spec)
    daily = next(page for page in pages if page.dest == "2026-07-15")
    notes = next(page for page in pages if page.dest == "2026-07-15-notes-1")
    assert any(isinstance(item, Schedule) for item in daily.components)
    assert any(isinstance(item, Notes) for item in daily.components)
    prio = next(item for item in daily.components if isinstance(item, Priorities))
    assert prio.label == "Priorities"
    assert prio.rows == 6
    mini = next(item for item in daily.components if isinstance(item, AnnualMonth))
    assert mini.month == 7
    assert mini.highlight_day == 15
    assert mini.dest == "month-2026-07"
    assert mini.weekday_labels[0] == "Mon"
    assert not any(isinstance(item, AnnualMonth) for item in notes.components)
    assert not any(isinstance(item, Schedule) for item in notes.components)
    assert not any(isinstance(item, Priorities) for item in notes.components)


def test_daily_mini_links_and_highlight():
    spec = Spec(notes_pages=1)
    pages = YearPlanner().pages(spec)
    july = next(
        item
        for page in pages
        if page.dest == "2026-07-15"
        for item in page.components
        if isinstance(item, AnnualMonth)
    )
    cells = [cell for week in july.weeks for cell in week]
    here = next(cell for cell in cells if cell.in_month and cell.day == 15)
    assert here.dest is None
    fourteen = next(cell for cell in cells if cell.in_month and cell.day == 14)
    assert fourteen.dest == "2026-07-14"
    june_30 = next(cell for cell in cells if not cell.in_month and cell.day == 30)
    assert june_30.dest == "2026-06-30"
    ink = RecordingPlotter()
    _paint_mini_month(ink, Rect(4, 20, 36, 34), july)
    links = ink.links()
    assert "month-2026-07" in links
    assert "2026-07-14" in links
    assert "2026-07-16" in links
    assert "2026-06-30" in links
    assert "2026-07-15" not in links
    fills = [op for op in ink.ops if op[0] == "rect" and op[3] and op[5] == 0.0]
    assert fills


def test_daily_mini_skips_unpressed_adjacent_days():
    spec = Spec(notes_pages=1)
    pages = YearPlanner().pages(spec)
    jan = next(
        item
        for page in pages
        if page.dest == "2026-01-01"
        for item in page.components
        if isinstance(item, AnnualMonth)
    )
    cells = [cell for week in jan.weeks for cell in week]
    dec = [cell for cell in cells if not cell.in_month and cell.day in {29, 30, 31}]
    assert dec
    assert all(cell.dest is None for cell in dec)
    assert next(cell for cell in cells if cell.in_month and cell.day == 1).dest is None
    assert (
        next(cell for cell in cells if cell.in_month and cell.day == 2).dest
        == "2026-01-02"
    )


def test_daily_left_column_split():
    well = well_rect(NOMAD)
    left, right = columns(well, 2, gap=COL_GAP, weights=DAILY_COL_WEIGHTS)
    sched, mini = daily_left_seats(left)
    assert left.w == pytest.approx(36.6758, abs=0.02)
    assert mini.h == pytest.approx(DAILY_MINI_H)
    assert sched.h == pytest.approx(left.h - DAILY_MINI_H - DAILY_MINI_GAP)
    assert sched.bottom + DAILY_MINI_GAP == pytest.approx(mini.y)
    assert mini.bottom == pytest.approx(left.bottom)
    assert right.h == pytest.approx(well.h)


def test_daily_right_column_priorities_over_notes():
    well = well_rect(NOMAD)
    _left, right = columns(well, 2, gap=COL_GAP, weights=DAILY_COL_WEIGHTS)
    prio, notes = daily_right_seats(right, 6)
    assert prio.h == pytest.approx(checklist_content_height(6))
    assert prio.y == pytest.approx(right.y)
    assert notes.y == pytest.approx(prio.bottom + DAILY_PRIO_GAP)
    assert notes.bottom == pytest.approx(right.bottom)
    ink = RecordingPlotter()
    paint_priorities(ink, prio, Priorities(label="Priorities", rows=6))
    ticks = [op for op in ink.ops if op[0] == "rect" and op[2] and op[1].w == TICK]
    assert len(ticks) == 6
    labels = [op[2] for op in ink.ops if op[0] == "text"]
    assert "Priorities" in labels
    assert Spec().priority_rows == 6
    assert Spec.from_mapping({"daily": {"priority_rows": 5}}).priority_rows == 5


def test_daily_page_hours_span_default_0700_1600():
    spec = Spec()
    assert spec.schedule.start == time(7, 0)
    assert spec.schedule.stop == time(16, 0)
    page = DailySection(spec).pages_for(date(2026, 7, 15))[0]
    hours = next(item.hours for item in page.components if isinstance(item, Schedule))
    assert hours == tuple(range(7, 17))

    parsed = Spec.from_mapping(
        {"daily": {"schedule": {"from": time(7, 0), "to": time(16, 0)}}}
    )
    page = DailySection(parsed).pages_for(date(2026, 1, 2))[0]
    hours = next(item.hours for item in page.components if isinstance(item, Schedule))
    assert hours == tuple(range(7, 17))


def _schedule_on(page) -> Schedule:
    return next(item for item in page.components if isinstance(item, Schedule))


def _wash_fills(ink: RecordingPlotter) -> list:
    return [
        op
        for op in ink.ops
        if op[0] == "rect" and op[3] and not op[2] and op[5] == pytest.approx(WASH)
    ]


def test_daily_omits_work_hours_and_paints_no_shade():
    spec = Spec()
    assert spec.work_hours is None
    page = DailySection(spec).pages_for(date(2026, 7, 15))[0]
    schedule = _schedule_on(page)
    assert schedule.work_hours is None
    ink = RecordingPlotter()
    paint_schedule(ink, Rect(4, 20, 36, 90), schedule)
    assert _wash_fills(ink) == []


def test_daily_carries_work_hours_bound_and_shades_intersecting_bands():
    spec = Spec.from_mapping(
        {"daily": {"work_hours": {"from": time(9, 0), "to": time(17, 0)}}}
    )
    assert spec.work_hours is not None
    assert spec.work_hours.as_tuple() == (time(9, 0), time(17, 0))
    page = DailySection(spec).pages_for(date(2026, 7, 15))[0]
    schedule = _schedule_on(page)
    assert schedule.hours == tuple(range(7, 17))
    assert schedule.work_hours == spec.work_hours
    ink = RecordingPlotter()
    paint_schedule(ink, Rect(4, 20, 36, 90), schedule)
    washes = _wash_fills(ink)
    # Painted 07–16; work 09:00–17:00 overlaps 09–16 (not 07–08).
    assert len(washes) == 8
    labels = [op for op in ink.ops if op[0] == "text" and op[2].strip().isdigit()]
    shaded_hours = {
        int(label[2].strip())
        for wash in washes
        for label in labels
        if label[1].y == pytest.approx(wash[1].y)
    }
    assert shaded_hours == set(range(9, 17))


def test_daily_partial_work_hours_shades_only_overlapping_rows():
    work = Clock.parse({"from": time(9, 30), "to": time(11, 30)})
    schedule = Schedule(label="Schedule", hours=tuple(range(7, 17)), work_hours=work)
    ink = RecordingPlotter()
    paint_schedule(ink, Rect(4, 20, 36, 90), schedule)
    washes = _wash_fills(ink)
    labels = [op for op in ink.ops if op[0] == "text" and op[2].strip().isdigit()]
    shaded_hours = {
        int(label[2].strip())
        for wash in washes
        for label in labels
        if label[1].y == pytest.approx(wash[1].y)
    }
    assert shaded_hours == {9, 10, 11}
