"""Planner layout: device chrome + seat, then painters."""

from typing import override

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
from parch.sections.visit import PageVisitor, accept

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
        """Ink one page by accepting a closed paint visitor."""
        plotter.ramp = self.ramp
        accept(page, _PaintVisitor(self.ramp, plotter, device))


class _PaintVisitor(PageVisitor[None]):
    """Full-bleed kinds skip chrome; every other kind paints header, nav, then well."""

    def __init__(self, ramp: TypeRamp, plotter: Plotter, device: Device) -> None:
        self._ramp = ramp
        self._plotter = plotter
        self._device = device

    def _chrome(self, page: Page) -> Rect:
        """Header and nav, then the writable well."""
        paint_header(
            self._plotter,
            self._device,
            page.title,
            _header_meta(page),
            _header_meta_dest(page),
            ramp=self._ramp,
            chip=_header_chip(page),
            chip_dest=_header_chip_dest(page),
        )
        paint_nav(
            self._plotter,
            self._device,
            strip_items(page),
            strip_active(page.kind),
            ramp=self._ramp,
        )
        return well_rect(self._device)

    def _engineering(self, page: Page) -> None:
        paint_engineering_pad(
            self._plotter, self._device, _one(page, EngineeringPad), ramp=self._ramp
        )

    @override
    def visit_cover(self, page: Page) -> None:
        paint_cover(
            self._plotter, self._device, _one(page, CoverTitle), ramp=self._ramp
        )

    @override
    def visit_engineering_front(self, page: Page) -> None:
        self._engineering(page)

    @override
    def visit_engineering_back(self, page: Page) -> None:
        self._engineering(page)

    @override
    def visit_steno(self, page: Page) -> None:
        paint_steno_pad(
            self._plotter, self._device, _one(page, StenoPad), ramp=self._ramp
        )

    @override
    def visit_dotgrid(self, page: Page) -> None:
        paint_dotgrid_page(
            self._plotter, self._device, _one(page, DotGridPad), ramp=self._ramp
        )

    @override
    def visit_lined(self, page: Page) -> None:
        paint_lined_page(
            self._plotter, self._device, _one(page, LinedPad), ramp=self._ramp
        )

    @override
    def visit_annual(self, page: Page) -> None:
        paint_annual(
            self._plotter, self._chrome(page), _one(page, AnnualGrid), ramp=self._ramp
        )

    @override
    def visit_favorites(self, page: Page) -> None:
        paint_favorites(
            self._plotter,
            self._chrome(page),
            _one(page, FavoritesPage),
            ramp=self._ramp,
        )

    @override
    def visit_my_100(self, page: Page) -> None:
        paint_my_100(
            self._plotter, self._chrome(page), _one(page, My100Page), ramp=self._ramp
        )

    @override
    def visit_checkoff_365(self, page: Page) -> None:
        paint_checkoff_365(
            self._plotter, self._chrome(page), _one(page, Checkoff365), ramp=self._ramp
        )

    @override
    def visit_projects_index(self, page: Page) -> None:
        paint_projects_index(
            self._plotter,
            self._chrome(page),
            _one(page, ProjectsIndex),
            ramp=self._ramp,
        )

    @override
    def visit_project(self, page: Page) -> None:
        paint_project(
            self._plotter,
            self._chrome(page),
            _one(page, ProjectsBoard),
            ramp=self._ramp,
        )

    @override
    def visit_meetings_index(self, page: Page) -> None:
        paint_meetings_index(
            self._plotter, self._chrome(page), _one(page, MeetingIndex), ramp=self._ramp
        )

    @override
    def visit_meeting(self, page: Page) -> None:
        paint_meeting(
            self._plotter,
            self._chrome(page),
            _one(page, MeetingAgenda),
            ramp=self._ramp,
        )

    @override
    def visit_tasks_index(self, page: Page) -> None:
        paint_tasks_index(
            self._plotter, self._chrome(page), _one(page, TasksIndex), ramp=self._ramp
        )

    @override
    def visit_task(self, page: Page) -> None:
        paint_task(
            self._plotter,
            self._chrome(page),
            _one(page, TasksWeekPage),
            ramp=self._ramp,
        )

    @override
    def visit_review_index(self, page: Page) -> None:
        paint_review_index(
            self._plotter, self._chrome(page), _one(page, ReviewIndex), ramp=self._ramp
        )

    @override
    def visit_review(self, page: Page) -> None:
        paint_review(
            self._plotter,
            self._chrome(page),
            _one(page, ReviewWeekPage),
            ramp=self._ramp,
        )

    @override
    def visit_quarter(self, page: Page) -> None:
        paint_quarter(
            self._plotter, self._chrome(page), _one(page, QuarterGrid), ramp=self._ramp
        )

    @override
    def visit_month(self, page: Page) -> None:
        paint_month_grid(
            self._plotter, self._chrome(page), _one(page, MonthGrid), ramp=self._ramp
        )

    @override
    def visit_habits(self, page: Page) -> None:
        paint_habit_grid(
            self._plotter, self._chrome(page), _one(page, HabitGrid), ramp=self._ramp
        )

    @override
    def visit_weekly(self, page: Page) -> None:
        paint_week(
            self._plotter, self._chrome(page), _one(page, WeekStrip), ramp=self._ramp
        )

    @override
    def visit_daily(self, page: Page) -> None:
        well = self._chrome(page)
        paint_daily(
            self._plotter,
            well,
            _one(page, Schedule),
            _one(page, AnnualMonth),
            _one(page, Priorities),
            _one(page, Notes),
            ramp=self._ramp,
        )

    @override
    def visit_daily_notes(self, page: Page) -> None:
        paint_notes(
            self._plotter, self._chrome(page), _one(page, Notes), ramp=self._ramp
        )

    @override
    def visit_bujo_key(self, page: Page) -> None:
        paint_bujo_key(
            self._plotter, self._chrome(page), _one(page, BujoKey), ramp=self._ramp
        )

    @override
    def visit_bujo_index(self, page: Page) -> None:
        paint_bujo_index(
            self._plotter, self._chrome(page), _one(page, BujoIndex), ramp=self._ramp
        )

    @override
    def visit_future_log(self, page: Page) -> None:
        paint_future_log(
            self._plotter,
            self._chrome(page),
            _one(page, FutureLogPage),
            ramp=self._ramp,
        )

    @override
    def visit_monthly_log(self, page: Page) -> None:
        paint_monthly_calendar_list(
            self._plotter,
            self._chrome(page),
            _one(page, MonthlyCalendarList),
            ramp=self._ramp,
        )

    @override
    def visit_monthly_tasks(self, page: Page) -> None:
        paint_monthly_task_well(
            self._plotter,
            self._chrome(page),
            _one(page, MonthlyTaskWell),
            ramp=self._ramp,
        )

    @override
    def visit_rapid_log(self, page: Page) -> None:
        paint_rapid_log(
            self._plotter, self._chrome(page), _one(page, RapidLogPage), ramp=self._ramp
        )

    @override
    def visit_collection(self, page: Page) -> None:
        paint_collection(
            self._plotter,
            self._chrome(page),
            _one(page, CollectionLeaf),
            ramp=self._ramp,
        )


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
