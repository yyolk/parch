"""Planner layout: device chrome + seat, then painters."""

from parch.calendar import quarter_of, short_date_range
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
from parch.devices.nomad import Device
from parch.fonts.ramp import JostRamp, TypeRamp
from parch.geom import Rect
from parch.tracks import columns, rows
from parch.layouts.planner.painters import (
    checklist_content_height,
    _paint_mini_month,
    paint_annual,
    paint_cover,
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
    paint_toolbar,
    strip_active,
    strip_items,
    well_rect,
)
from parch.plotter.protocol import Plotter
from parch.sections.page import Page

COL_GAP = 3.0
DAILY_MINI_H = 34.0
DAILY_MINI_GAP = 2.2
DAILY_COL_WEIGHTS = (0.34, 0.66)
DAILY_PRIO_GAP = 2.2


class PlannerLayout:
    """Seat components below the unmarked toolbar. Cover skips slab/nav.

    Holds an explicit ``TypeRamp`` (default ``JostRamp``). Each ``paint``
    binds ``ramp.for_page(page.kind)`` and passes that ``BoundRamp`` into
    painters — no threadlocals, no kind on ``ink()``. Cover / header / year /
    month / week / daily / projects read steps from the PageKind table.
    Dual-font ramps are future work; ``family`` stays on the ink.
    """

    def __init__(self, ramp: TypeRamp | None = None) -> None:
        self.ramp: TypeRamp = JostRamp() if ramp is None else ramp

    def paint(self, page: Page, plotter: Plotter, device: Device) -> None:
        paint_toolbar(plotter, device)
        bound = self.ramp.for_page(page.kind)
        match page.kind:
            case "cover":
                paint_cover(plotter, device, _one(page, CoverTitle), ramp=bound)
            case _:
                paint_header(
                    plotter,
                    device,
                    page.title,
                    _header_meta(page),
                    _header_meta_dest(page),
                    ramp=bound,
                    chip=_header_chip(page),
                    chip_dest=_header_chip_dest(page),
                )
                paint_nav(plotter, device, strip_items(page), strip_active(page.kind))
                well = well_rect(device)
                self._paint_well(page, plotter, well, ramp=bound)

    def _paint_well(self, page: Page, plotter: Plotter, well: Rect, *, ramp: TypeRamp) -> None:
        match page.kind:
            case "annual":
                paint_annual(plotter, well, _one(page, AnnualGrid), ramp=ramp)
            case "projects_index":
                paint_projects_index(plotter, well, _one(page, ProjectsIndex), ramp=ramp)
            case "project":
                paint_project(plotter, well, _one(page, ProjectsBoard), ramp=ramp)
            case "meetings_index":
                paint_meetings_index(plotter, well, _one(page, MeetingIndex))
            case "meeting":
                paint_meeting(plotter, well, _one(page, MeetingAgenda))
            case "tasks_index":
                paint_tasks_index(plotter, well, _one(page, TasksIndex))
            case "task":
                paint_task(plotter, well, _one(page, TasksWeekPage))
            case "review_index":
                paint_review_index(plotter, well, _one(page, ReviewIndex))
            case "review":
                paint_review(plotter, well, _one(page, ReviewWeekPage))
            case "quarter":
                paint_quarter(plotter, well, _one(page, QuarterGrid), ramp=ramp)
            case "month":
                paint_month_grid(plotter, well, _one(page, MonthGrid), ramp=ramp)
            case "habits":
                paint_habit_grid(plotter, well, _one(page, HabitGrid))
            case "weekly":
                paint_week(plotter, well, _one(page, WeekStrip), ramp=ramp)
            case "daily":
                schedule = _one(page, Schedule)
                notes = _one(page, Notes)
                mini = _one(page, AnnualMonth)
                priorities = _one(page, Priorities)
                left, right = columns(well, 2, gap=COL_GAP, weights=DAILY_COL_WEIGHTS)
                sched_box, mini_box = daily_left_seats(left)
                prio_box, notes_box = daily_right_seats(right, priorities.rows)
                paint_schedule(plotter, sched_box, schedule, ramp=ramp)
                _paint_mini_month(plotter, mini_box, mini, ramp=ramp)
                paint_priorities(plotter, prio_box, priorities, ramp=ramp)
                paint_notes(plotter, notes_box, notes, ramp=ramp)
            case "daily_notes":
                paint_notes(plotter, well, _one(page, Notes), ramp=ramp)
            case _:
                raise ValueError(f"unknown page kind {page.kind!r}")


def daily_left_seats(left: Rect) -> tuple[Rect, Rect]:
    """Schedule flex over a compact year-density mini-month."""
    return rows(
        left,
        2,
        gap=DAILY_MINI_GAP,
        weights=(left.h - DAILY_MINI_H - DAILY_MINI_GAP, DAILY_MINI_H),
    )


def daily_right_seats(right: Rect, priority_rows: int) -> tuple[Rect, Rect]:
    """Content-height Priorities over flex Notes. No dead band under the last tick."""
    prio_h = checklist_content_height(priority_rows)
    return rows(
        right,
        2,
        gap=DAILY_PRIO_GAP,
        weights=(prio_h, max(right.h - prio_h - DAILY_PRIO_GAP, 1)),
    )


def _header_meta(page: Page) -> str:
    match page.kind:
        case "annual":
            return "Q1–Q4"
        case "projects_index":
            return str(_one(page, ProjectsIndex).year)
        case "project":
            return str(_one(page, ProjectsBoard).year)
        case "meetings_index":
            return str(_one(page, MeetingIndex).year)
        case "meeting":
            return str(_one(page, MeetingAgenda).year)
        case "tasks_index":
            return f"Q{_one(page, TasksIndex).quarter}"
        case "task":
            return str(_one(page, TasksWeekPage).year)
        case "review_index":
            return str(_one(page, ReviewIndex).year)
        case "review":
            return str(_one(page, ReviewWeekPage).year)
        case "quarter":
            return ""
        case "month":
            month = _one(page, MonthGrid).month
            return f"Q{quarter_of(month)}"
        case "habits":
            month = _one(page, HabitGrid).month
            return f"Q{quarter_of(month)}"
        case "weekly":
            week = _one(page, WeekStrip)
            return short_date_range(week.monday, week.sunday)
        case "daily":
            return page.dest[:4]
        case "daily_notes":
            label = _one(page, Notes).label
            return label.rsplit(" ", 1)[-1] if " " in label else page.dest[:4]
        case _:
            return ""


def _header_meta_dest(page: Page) -> str | None:
    match page.kind:
        case "annual":
            return _one(page, AnnualGrid).quarter_dest
        case "month":
            return _one(page, MonthGrid).quarter_dest
        case "habits":
            return _one(page, HabitGrid).quarter_dest
        case _:
            return None


def _header_chip(page: Page) -> str:
    match page.kind:
        case "month":
            return "Habits"
        case "habits":
            return "Month"
        case "project":
            number = _one(page, ProjectsBoard).number
            return f"{number:02d}" if number else ""
        case "meeting":
            number = _one(page, MeetingAgenda).number
            return f"{number:02d}" if number else ""
        case "task":
            week = _one(page, TasksWeekPage)
            return f"W{week.iso_week:02d}"
        case "review":
            week = _one(page, ReviewWeekPage)
            return f"W{week.iso_week:02d}"
        case _:
            return ""


def _header_chip_dest(page: Page) -> str | None:
    match page.kind:
        case "month":
            return _one(page, MonthGrid).habits_dest
        case "habits":
            return _one(page, HabitGrid).month_dest
        case "project":
            return _one(page, ProjectsBoard).index_dest or None
        case "meeting":
            return _one(page, MeetingAgenda).index_dest or None
        case "task":
            return _one(page, TasksWeekPage).index_dest or None
        case "review":
            return _one(page, ReviewWeekPage).index_dest or None
        case _:
            return None


def _one[T](page: Page, typ: type[T]) -> T:
    for item in page.components:
        if isinstance(item, typ):
            return item
    raise TypeError(f"{page.kind} page missing {typ.__name__}")
