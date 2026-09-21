"""Planner layout: device chrome + seat, then painters."""

from typing import assert_never

from parch.calendar import quarter_of, short_date_range
from parch.components import (
    AnnualGrid,
    AnnualMonth,
    BujoIndex,
    BujoKey,
    Checkoff365,
    CollectionLeaf,
    CoverTitle,
    DotGridPad,
    EngineeringPad,
    FavoritesPage,
    FutureLogPage,
    HabitGrid,
    MeetingAgenda,
    MeetingIndex,
    MonthGrid,
    MonthlyCalendarList,
    MonthlyTaskWell,
    My100Page,
    Notes,
    Priorities,
    ProjectsBoard,
    ProjectsIndex,
    QuarterGrid,
    RapidLogPage,
    ReviewIndex,
    ReviewWeekPage,
    Schedule,
    StenoPad,
    TasksIndex,
    TasksWeekPage,
    WeekStrip,
)
from parch.devices.registry import Device
from parch.fonts.ramp import EffectiveRamp, TypeRamp
from parch.geom import Rect
from parch.layouts.planner.painters import (
    COL_GAP,
    DAILY_COL_WEIGHTS,
    DAILY_MINI_GAP,
    DAILY_MINI_H,
    DAILY_PRIO_GAP,
    checklist_content_height,
    daily_left_seats,
    daily_right_seats,
    paint_annual,
    paint_bujo_index,
    paint_bujo_key,
    paint_checkoff_365,
    paint_collection,
    paint_cover,
    paint_daily,
    paint_dotgrid_page,
    paint_engineering_pad,
    paint_favorites,
    paint_future_log,
    paint_habit_grid,
    paint_header,
    paint_meeting,
    paint_meetings_index,
    paint_month_grid,
    paint_monthly_calendar_list,
    paint_monthly_task_well,
    paint_my_100,
    paint_nav,
    paint_notes,
    paint_project,
    paint_projects_index,
    paint_quarter,
    paint_rapid_log,
    paint_review,
    paint_review_index,
    paint_steno_pad,
    paint_task,
    paint_tasks_index,
    paint_week,
    strip_active,
    strip_items,
    well_rect,
)
from parch.plotter.protocol import Plotter
from parch.sections.page import Page, PageKind

__all__ = [
    "COL_GAP",
    "DAILY_COL_WEIGHTS",
    "DAILY_MINI_GAP",
    "DAILY_MINI_H",
    "DAILY_PRIO_GAP",
    "PlannerLayout",
    "checklist_content_height",
    "daily_left_seats",
    "daily_right_seats",
    "well_rect",
]


class PlannerLayout:
    """Seat components below the INK header. Cover and pad faces skip header/nav.

    Holds an explicit ``TypeRamp`` (default ``EffectiveRamp``) and binds it
    onto the plotter. Painters pass ``TypeRef`` / ink on the closed TypeStep
    ladder. Press may hand in an ``EffectiveRamp`` (defaults ⊕ toml ⊕
    proof) at ``device.root_body``. ``family`` stays on the resolved ink.
    """

    def __init__(self, ramp: TypeRamp | None = None) -> None:
        self.ramp: TypeRamp = EffectiveRamp() if ramp is None else ramp

    def paint(self, page: Page, plotter: Plotter, device: Device) -> None:
        plotter.ramp = self.ramp
        match page.kind:
            case PageKind.COVER:
                paint_cover(plotter, device, _one(page, CoverTitle), ramp=self.ramp)
            case PageKind.ENGINEERING_FRONT | PageKind.ENGINEERING_BACK:
                paint_engineering_pad(
                    plotter, device, _one(page, EngineeringPad), ramp=self.ramp
                )
            case PageKind.STENO:
                paint_steno_pad(plotter, device, _one(page, StenoPad), ramp=self.ramp)
            case PageKind.DOTGRID:
                paint_dotgrid_page(
                    plotter, device, _one(page, DotGridPad), ramp=self.ramp
                )
            case (
                PageKind.ANNUAL
                | PageKind.FAVORITES
                | PageKind.MY_100
                | PageKind.CHECKOFF_365
                | PageKind.PROJECTS_INDEX
                | PageKind.PROJECT
                | PageKind.MEETINGS_INDEX
                | PageKind.MEETING
                | PageKind.TASKS_INDEX
                | PageKind.TASK
                | PageKind.REVIEW_INDEX
                | PageKind.REVIEW
                | PageKind.QUARTER
                | PageKind.MONTH
                | PageKind.HABITS
                | PageKind.WEEKLY
                | PageKind.DAILY
                | PageKind.DAILY_NOTES
                | PageKind.BUJO_KEY
                | PageKind.BUJO_INDEX
                | PageKind.FUTURE_LOG
                | PageKind.MONTHLY_LOG
                | PageKind.MONTHLY_TASKS
                | PageKind.RAPID_LOG
                | PageKind.COLLECTION
            ):
                paint_header(
                    plotter,
                    device,
                    page.title,
                    _header_meta(page),
                    _header_meta_dest(page),
                    ramp=self.ramp,
                    chip=_header_chip(page),
                    chip_dest=_header_chip_dest(page),
                )
                paint_nav(
                    plotter,
                    device,
                    strip_items(page),
                    strip_active(page.kind),
                    ramp=self.ramp,
                )
                well = well_rect(device)
                self._paint_well(page, plotter, well)
            case _:
                assert_never(page.kind)

    def _paint_well(self, page: Page, plotter: Plotter, well: Rect) -> None:
        ramp = self.ramp
        match page.kind:
            case PageKind.ANNUAL:
                paint_annual(plotter, well, _one(page, AnnualGrid), ramp=ramp)
            case PageKind.FAVORITES:
                paint_favorites(plotter, well, _one(page, FavoritesPage), ramp=ramp)
            case PageKind.MY_100:
                paint_my_100(plotter, well, _one(page, My100Page), ramp=ramp)
            case PageKind.CHECKOFF_365:
                paint_checkoff_365(plotter, well, _one(page, Checkoff365), ramp=ramp)
            case PageKind.PROJECTS_INDEX:
                paint_projects_index(
                    plotter, well, _one(page, ProjectsIndex), ramp=ramp
                )
            case PageKind.PROJECT:
                paint_project(plotter, well, _one(page, ProjectsBoard), ramp=ramp)
            case PageKind.MEETINGS_INDEX:
                paint_meetings_index(plotter, well, _one(page, MeetingIndex), ramp=ramp)
            case PageKind.MEETING:
                paint_meeting(plotter, well, _one(page, MeetingAgenda), ramp=ramp)
            case PageKind.TASKS_INDEX:
                paint_tasks_index(plotter, well, _one(page, TasksIndex), ramp=ramp)
            case PageKind.TASK:
                paint_task(plotter, well, _one(page, TasksWeekPage), ramp=ramp)
            case PageKind.REVIEW_INDEX:
                paint_review_index(plotter, well, _one(page, ReviewIndex), ramp=ramp)
            case PageKind.REVIEW:
                paint_review(plotter, well, _one(page, ReviewWeekPage), ramp=ramp)
            case PageKind.QUARTER:
                paint_quarter(plotter, well, _one(page, QuarterGrid), ramp=ramp)
            case PageKind.MONTH:
                paint_month_grid(plotter, well, _one(page, MonthGrid), ramp=ramp)
            case PageKind.HABITS:
                paint_habit_grid(plotter, well, _one(page, HabitGrid), ramp=ramp)
            case PageKind.WEEKLY:
                paint_week(plotter, well, _one(page, WeekStrip), ramp=ramp)
            case PageKind.DAILY:
                paint_daily(
                    plotter,
                    well,
                    _one(page, Schedule),
                    _one(page, AnnualMonth),
                    _one(page, Priorities),
                    _one(page, Notes),
                    ramp=ramp,
                )
            case PageKind.DAILY_NOTES:
                paint_notes(plotter, well, _one(page, Notes), ramp=ramp)
            case PageKind.BUJO_KEY:
                paint_bujo_key(plotter, well, _one(page, BujoKey), ramp=ramp)
            case PageKind.BUJO_INDEX:
                paint_bujo_index(plotter, well, _one(page, BujoIndex), ramp=ramp)
            case PageKind.FUTURE_LOG:
                paint_future_log(plotter, well, _one(page, FutureLogPage), ramp=ramp)
            case PageKind.MONTHLY_LOG:
                paint_monthly_calendar_list(
                    plotter, well, _one(page, MonthlyCalendarList), ramp=ramp
                )
            case PageKind.MONTHLY_TASKS:
                paint_monthly_task_well(
                    plotter, well, _one(page, MonthlyTaskWell), ramp=ramp
                )
            case PageKind.RAPID_LOG:
                paint_rapid_log(plotter, well, _one(page, RapidLogPage), ramp=ramp)
            case PageKind.COLLECTION:
                paint_collection(plotter, well, _one(page, CollectionLeaf), ramp=ramp)
            case (
                PageKind.COVER
                | PageKind.ENGINEERING_FRONT
                | PageKind.ENGINEERING_BACK
                | PageKind.STENO
                | PageKind.DOTGRID
            ):
                raise ValueError(f"{page.kind} has no well")
            case _:
                assert_never(page.kind)


def _header_meta(page: Page) -> str:
    match page.kind:
        case PageKind.ANNUAL:
            return "Q1–Q4"
        case PageKind.FAVORITES:
            return str(_one(page, FavoritesPage).year)
        case PageKind.MY_100:
            return str(_one(page, My100Page).year)
        case PageKind.CHECKOFF_365:
            return str(_one(page, Checkoff365).year)
        case PageKind.PROJECTS_INDEX:
            return str(_one(page, ProjectsIndex).year)
        case PageKind.PROJECT:
            return str(_one(page, ProjectsBoard).year)
        case PageKind.MEETINGS_INDEX:
            return str(_one(page, MeetingIndex).year)
        case PageKind.MEETING:
            return str(_one(page, MeetingAgenda).year)
        case PageKind.TASKS_INDEX:
            return f"Q{_one(page, TasksIndex).quarter}"
        case PageKind.TASK:
            return str(_one(page, TasksWeekPage).year)
        case PageKind.REVIEW_INDEX:
            return str(_one(page, ReviewIndex).year)
        case PageKind.REVIEW:
            return str(_one(page, ReviewWeekPage).year)
        case PageKind.QUARTER:
            return ""
        case PageKind.MONTH:
            month = _one(page, MonthGrid).month
            return f"Q{quarter_of(month)}"
        case PageKind.HABITS:
            grid = _one(page, HabitGrid)
            return f"Q{quarter_of(grid.month)}" if grid.quarter_dest else ""
        case PageKind.BUJO_KEY:
            return page.dest.rsplit("-", 1)[-1]
        case PageKind.BUJO_INDEX:
            index = _one(page, BujoIndex)
            return f"{index.page}/{index.pages}"
        case PageKind.FUTURE_LOG:
            future = _one(page, FutureLogPage)
            return f"{future.page}/{future.pages}"
        case PageKind.MONTHLY_LOG:
            return "Tasks"
        case PageKind.MONTHLY_TASKS:
            return _one(page, MonthlyTaskWell).month_name[:3]
        case PageKind.RAPID_LOG:
            return page.dest[:4]
        case PageKind.COLLECTION:
            return str(_one(page, CollectionLeaf).year)
        case PageKind.WEEKLY:
            week = _one(page, WeekStrip)
            return short_date_range(week.monday, week.sunday)
        case PageKind.DAILY:
            return page.dest[:4]
        case PageKind.DAILY_NOTES:
            label = _one(page, Notes).label
            return label.rsplit(" ", 1)[-1] if " " in label else page.dest[:4]
        case _:
            return ""


def _header_meta_dest(page: Page) -> str | None:
    match page.kind:
        case PageKind.ANNUAL:
            return _one(page, AnnualGrid).quarter_dest
        case PageKind.MONTH:
            return _one(page, MonthGrid).quarter_dest
        case PageKind.HABITS:
            return _one(page, HabitGrid).quarter_dest
        case PageKind.MONTHLY_LOG:
            return _one(page, MonthlyCalendarList).tasks_dest
        case PageKind.MONTHLY_TASKS:
            return _one(page, MonthlyTaskWell).calendar_dest
        case _:
            return None


def _header_chip(page: Page) -> str:
    match page.kind:
        case PageKind.MY_100:
            leaf = _one(page, My100Page)
            return f"{leaf.page:02d}" if leaf.pages > 1 else ""
        case PageKind.PROJECT:
            number = _one(page, ProjectsBoard).number
            return f"{number:02d}" if number else ""
        case PageKind.MEETING:
            number = _one(page, MeetingAgenda).number
            return f"{number:02d}" if number else ""
        case PageKind.TASK:
            week = _one(page, TasksWeekPage)
            return f"W{week.iso_week:02d}"
        case PageKind.REVIEW:
            week = _one(page, ReviewWeekPage)
            return f"W{week.iso_week:02d}"
        case PageKind.COLLECTION:
            number = _one(page, CollectionLeaf).number
            return f"{number:02d}"
        case _:
            return ""


def _header_chip_dest(page: Page) -> str | None:
    match page.kind:
        case PageKind.MY_100:
            leaf = _one(page, My100Page)
            return leaf.index_dest if leaf.pages > 1 else None
        case PageKind.PROJECT:
            return _one(page, ProjectsBoard).index_dest or None
        case PageKind.MEETING:
            return _one(page, MeetingAgenda).index_dest or None
        case PageKind.TASK:
            return _one(page, TasksWeekPage).index_dest or None
        case PageKind.REVIEW:
            return _one(page, ReviewWeekPage).index_dest or None
        case PageKind.COLLECTION:
            return _one(page, CollectionLeaf).index_dest or None
        case _:
            return None


def _one[T](page: Page, typ: type[T]) -> T:
    for item in page.components:
        if isinstance(item, typ):
            return item
    raise TypeError(f"{page.kind} page missing {typ.__name__}")
