"""Planner layout: device chrome + seat, then painters."""

from typing import assert_never

import parch.sections.kinds as kinds
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
    LinedPad,
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
    paint_lined_page,
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
from parch.sections.page import Page

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
        """Paint one page. The match is closed on ``PageKind``."""
        plotter.ramp = self.ramp
        match page.kind:
            case kinds.Cover():
                paint_cover(plotter, device, _one(page, CoverTitle), ramp=self.ramp)
            case kinds.EngineeringFront() | kinds.EngineeringBack():
                paint_engineering_pad(
                    plotter, device, _one(page, EngineeringPad), ramp=self.ramp
                )
            case kinds.Steno():
                paint_steno_pad(plotter, device, _one(page, StenoPad), ramp=self.ramp)
            case kinds.Dotgrid():
                paint_dotgrid_page(
                    plotter, device, _one(page, DotGridPad), ramp=self.ramp
                )
            case kinds.Lined():
                paint_lined_page(plotter, device, _one(page, LinedPad), ramp=self.ramp)
            case (
                kinds.Annual()
                | kinds.Favorites()
                | kinds.My100()
                | kinds.Checkoff365()
                | kinds.ProjectsIndex()
                | kinds.Project()
                | kinds.MeetingsIndex()
                | kinds.Meeting()
                | kinds.TasksIndex()
                | kinds.Task()
                | kinds.ReviewIndex()
                | kinds.Review()
                | kinds.Quarter()
                | kinds.Month()
                | kinds.Habits()
                | kinds.Weekly()
                | kinds.Daily()
                | kinds.DailyNotes()
                | kinds.BujoKey()
                | kinds.BujoIndex()
                | kinds.FutureLog()
                | kinds.MonthlyLog()
                | kinds.MonthlyTasks()
                | kinds.RapidLog()
                | kinds.Collection()
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
            case _ as other:
                assert_never(other)

    def _paint_well(self, page: Page, plotter: Plotter, well: Rect) -> None:
        """Paint the seated well. Full-bleed kinds never reach this match."""
        ramp = self.ramp
        match page.kind:
            case kinds.Annual():
                paint_annual(plotter, well, _one(page, AnnualGrid), ramp=ramp)
            case kinds.Favorites():
                paint_favorites(plotter, well, _one(page, FavoritesPage), ramp=ramp)
            case kinds.My100():
                paint_my_100(plotter, well, _one(page, My100Page), ramp=ramp)
            case kinds.Checkoff365():
                paint_checkoff_365(plotter, well, _one(page, Checkoff365), ramp=ramp)
            case kinds.ProjectsIndex():
                paint_projects_index(
                    plotter, well, _one(page, ProjectsIndex), ramp=ramp
                )
            case kinds.Project():
                paint_project(plotter, well, _one(page, ProjectsBoard), ramp=ramp)
            case kinds.MeetingsIndex():
                paint_meetings_index(plotter, well, _one(page, MeetingIndex), ramp=ramp)
            case kinds.Meeting():
                paint_meeting(plotter, well, _one(page, MeetingAgenda), ramp=ramp)
            case kinds.TasksIndex():
                paint_tasks_index(plotter, well, _one(page, TasksIndex), ramp=ramp)
            case kinds.Task():
                paint_task(plotter, well, _one(page, TasksWeekPage), ramp=ramp)
            case kinds.ReviewIndex():
                paint_review_index(plotter, well, _one(page, ReviewIndex), ramp=ramp)
            case kinds.Review():
                paint_review(plotter, well, _one(page, ReviewWeekPage), ramp=ramp)
            case kinds.Quarter():
                paint_quarter(plotter, well, _one(page, QuarterGrid), ramp=ramp)
            case kinds.Month():
                paint_month_grid(plotter, well, _one(page, MonthGrid), ramp=ramp)
            case kinds.Habits():
                paint_habit_grid(plotter, well, _one(page, HabitGrid), ramp=ramp)
            case kinds.Weekly():
                paint_week(plotter, well, _one(page, WeekStrip), ramp=ramp)
            case kinds.Daily():
                paint_daily(
                    plotter,
                    well,
                    _one(page, Schedule),
                    _one(page, AnnualMonth),
                    _one(page, Priorities),
                    _one(page, Notes),
                    ramp=ramp,
                )
            case kinds.DailyNotes():
                paint_notes(plotter, well, _one(page, Notes), ramp=ramp)
            case kinds.BujoKey():
                paint_bujo_key(plotter, well, _one(page, BujoKey), ramp=ramp)
            case kinds.BujoIndex():
                paint_bujo_index(plotter, well, _one(page, BujoIndex), ramp=ramp)
            case kinds.FutureLog():
                paint_future_log(plotter, well, _one(page, FutureLogPage), ramp=ramp)
            case kinds.MonthlyLog():
                paint_monthly_calendar_list(
                    plotter, well, _one(page, MonthlyCalendarList), ramp=ramp
                )
            case kinds.MonthlyTasks():
                paint_monthly_task_well(
                    plotter, well, _one(page, MonthlyTaskWell), ramp=ramp
                )
            case kinds.RapidLog():
                paint_rapid_log(plotter, well, _one(page, RapidLogPage), ramp=ramp)
            case kinds.Collection():
                paint_collection(plotter, well, _one(page, CollectionLeaf), ramp=ramp)
            case (
                kinds.Cover()
                | kinds.EngineeringFront()
                | kinds.EngineeringBack()
                | kinds.Steno()
                | kinds.Dotgrid()
                | kinds.Lined()
            ):
                raise AssertionError(page.kind)
            case _ as other:
                assert_never(other)


def _header_meta(page: Page) -> str:
    match page.kind:
        case "annual":
            return "Q1–Q4"
        case "favorites":
            return str(_one(page, FavoritesPage).year)
        case "my_100":
            return str(_one(page, My100Page).year)
        case "checkoff_365":
            return str(_one(page, Checkoff365).year)
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
            grid = _one(page, HabitGrid)
            return f"Q{quarter_of(grid.month)}" if grid.quarter_dest else ""
        case "bujo_key":
            return page.dest.rsplit("-", 1)[-1]
        case "bujo_index":
            index = _one(page, BujoIndex)
            return f"{index.page}/{index.pages}"
        case "future_log":
            future = _one(page, FutureLogPage)
            return f"{future.page}/{future.pages}"
        case "monthly_log":
            return "Tasks"
        case "monthly_tasks":
            return _one(page, MonthlyTaskWell).month_name[:3]
        case "rapid_log":
            return page.dest[:4]
        case "collection":
            return str(_one(page, CollectionLeaf).year)
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
        case "monthly_log":
            return _one(page, MonthlyCalendarList).tasks_dest
        case "monthly_tasks":
            return _one(page, MonthlyTaskWell).calendar_dest
        case _:
            return None


def _header_chip(page: Page) -> str:
    match page.kind:
        case "my_100":
            leaf = _one(page, My100Page)
            return f"{leaf.page:02d}" if leaf.pages > 1 else ""
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
        case "collection":
            number = _one(page, CollectionLeaf).number
            return f"{number:02d}"
        case _:
            return ""


def _header_chip_dest(page: Page) -> str | None:
    match page.kind:
        case "my_100":
            leaf = _one(page, My100Page)
            return leaf.index_dest if leaf.pages > 1 else None
        case "project":
            return _one(page, ProjectsBoard).index_dest or None
        case "meeting":
            return _one(page, MeetingAgenda).index_dest or None
        case "task":
            return _one(page, TasksWeekPage).index_dest or None
        case "review":
            return _one(page, ReviewWeekPage).index_dest or None
        case "collection":
            return _one(page, CollectionLeaf).index_dest or None
        case _:
            return None


def _one[T](page: Page, typ: type[T]) -> T:
    for item in page.components:
        if isinstance(item, typ):
            return item
    raise TypeError(f"{page.kind} page missing {typ.__name__}")
