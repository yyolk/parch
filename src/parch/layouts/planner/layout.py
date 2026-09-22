"""Planner layout: device chrome + seat, then painters."""

from typing import assert_never

from parch.calendar import quarter_of, short_date_range
from parch.components import (
    AnnualGrid,
    AnnualMonth,
    BujoIndex,
    BujoKey,
    Checkoff365,
    ChromeComponent,
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
    WellComponent,
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
    """Seat components below the INK header. Cover and pad leads skip header/nav.

    Holds an explicit ``TypeRamp`` (default ``EffectiveRamp``) and binds it
    onto the plotter. Painters pass ``TypeRef`` / ink on the closed TypeStep
    ladder. Press may hand in an ``EffectiveRamp`` (defaults ⊕ toml ⊕
    proof) at ``device.root_body``. ``family`` stays on the resolved ink.
    """

    def __init__(self, ramp: TypeRamp | None = None) -> None:
        self.ramp: TypeRamp = EffectiveRamp() if ramp is None else ramp

    def paint(self, page: Page, plotter: Plotter, device: Device) -> None:
        plotter.ramp = self.ramp
        match page.lead:
            case (
                CoverTitle() | EngineeringPad() | StenoPad() | DotGridPad() | LinedPad()
            ) as chrome:
                self._paint_chrome(chrome, plotter, device)
            case well:
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
                    strip_active(page),
                    ramp=self.ramp,
                )
                self._paint_well(page, plotter, well_rect(device), well)

    def _paint_chrome(
        self, chrome: ChromeComponent, plotter: Plotter, device: Device
    ) -> None:
        match chrome:
            case CoverTitle() as title:
                paint_cover(plotter, device, title, ramp=self.ramp)
            case EngineeringPad() as pad:
                paint_engineering_pad(plotter, device, pad, ramp=self.ramp)
            case StenoPad() as pad:
                paint_steno_pad(plotter, device, pad, ramp=self.ramp)
            case DotGridPad() as pad:
                paint_dotgrid_page(plotter, device, pad, ramp=self.ramp)
            case LinedPad() as pad:
                paint_lined_page(plotter, device, pad, ramp=self.ramp)
            case _ as unseen:
                assert_never(unseen)

    def _paint_well(
        self, page: Page, plotter: Plotter, well: Rect, lead: WellComponent
    ) -> None:
        ramp = self.ramp
        match lead:
            case AnnualGrid() as grid:
                paint_annual(plotter, well, grid, ramp=ramp)
            case FavoritesPage() as favorites:
                paint_favorites(plotter, well, favorites, ramp=ramp)
            case My100Page() as hundred:
                paint_my_100(plotter, well, hundred, ramp=ramp)
            case Checkoff365() as checkoff:
                paint_checkoff_365(plotter, well, checkoff, ramp=ramp)
            case ProjectsIndex() as index:
                paint_projects_index(plotter, well, index, ramp=ramp)
            case ProjectsBoard() as board:
                paint_project(plotter, well, board, ramp=ramp)
            case MeetingIndex() as index:
                paint_meetings_index(plotter, well, index, ramp=ramp)
            case MeetingAgenda() as agenda:
                paint_meeting(plotter, well, agenda, ramp=ramp)
            case TasksIndex() as index:
                paint_tasks_index(plotter, well, index, ramp=ramp)
            case TasksWeekPage() as week:
                paint_task(plotter, well, week, ramp=ramp)
            case ReviewIndex() as index:
                paint_review_index(plotter, well, index, ramp=ramp)
            case ReviewWeekPage() as week:
                paint_review(plotter, well, week, ramp=ramp)
            case QuarterGrid() as grid:
                paint_quarter(plotter, well, grid, ramp=ramp)
            case MonthGrid() as grid:
                paint_month_grid(plotter, well, grid, ramp=ramp)
            case HabitGrid() as grid:
                paint_habit_grid(plotter, well, grid, ramp=ramp)
            case WeekStrip() as week:
                paint_week(plotter, well, week, ramp=ramp)
            case Schedule() as schedule:
                paint_daily(
                    plotter,
                    well,
                    schedule,
                    _one(page, AnnualMonth),
                    _one(page, Priorities),
                    _one(page, Notes),
                    ramp=ramp,
                )
            case Notes() as notes:
                paint_notes(plotter, well, notes, ramp=ramp)
            case BujoKey() as key:
                paint_bujo_key(plotter, well, key, ramp=ramp)
            case BujoIndex() as index:
                paint_bujo_index(plotter, well, index, ramp=ramp)
            case FutureLogPage() as future:
                paint_future_log(plotter, well, future, ramp=ramp)
            case MonthlyCalendarList() as calendar:
                paint_monthly_calendar_list(plotter, well, calendar, ramp=ramp)
            case MonthlyTaskWell() as tasks:
                paint_monthly_task_well(plotter, well, tasks, ramp=ramp)
            case RapidLogPage() as rapid:
                paint_rapid_log(plotter, well, rapid, ramp=ramp)
            case CollectionLeaf() as leaf:
                paint_collection(plotter, well, leaf, ramp=ramp)
            case _ as unseen:
                assert_never(unseen)


def _header_meta(page: Page) -> str:
    match page.lead:
        case AnnualGrid():
            return "Q1–Q4"
        case FavoritesPage() as favorites:
            return str(favorites.year)
        case My100Page() as hundred:
            return str(hundred.year)
        case Checkoff365() as checkoff:
            return str(checkoff.year)
        case ProjectsIndex() as index:
            return str(index.year)
        case ProjectsBoard() as board:
            return str(board.year)
        case MeetingIndex() as index:
            return str(index.year)
        case MeetingAgenda() as agenda:
            return str(agenda.year)
        case TasksIndex() as index:
            return f"Q{index.quarter}"
        case TasksWeekPage() as week:
            return str(week.year)
        case ReviewIndex() as index:
            return str(index.year)
        case ReviewWeekPage() as week:
            return str(week.year)
        case QuarterGrid():
            return ""
        case MonthGrid() as month:
            return f"Q{quarter_of(month.month)}"
        case HabitGrid() as grid:
            return f"Q{quarter_of(grid.month)}" if grid.quarter_dest else ""
        case BujoKey():
            return page.dest.rsplit("-", 1)[-1]
        case BujoIndex() as index:
            return f"{index.page}/{index.pages}"
        case FutureLogPage() as future:
            return f"{future.page}/{future.pages}"
        case MonthlyCalendarList():
            return "Tasks"
        case MonthlyTaskWell() as tasks:
            return tasks.month_name[:3]
        case RapidLogPage():
            return page.dest[:4]
        case CollectionLeaf() as leaf:
            return str(leaf.year)
        case WeekStrip() as week:
            return short_date_range(week.monday, week.sunday)
        case Schedule():
            return page.dest[:4]
        case Notes() as notes:
            label = notes.label
            return label.rsplit(" ", 1)[-1] if " " in label else page.dest[:4]
        case CoverTitle() | EngineeringPad() | StenoPad() | DotGridPad() | LinedPad():
            return ""
        case _ as unseen:
            assert_never(unseen)


def _header_meta_dest(page: Page) -> str | None:
    match page.lead:
        case AnnualGrid() as grid:
            return grid.quarter_dest
        case MonthGrid() as month:
            return month.quarter_dest
        case HabitGrid() as grid:
            return grid.quarter_dest
        case MonthlyCalendarList() as calendar:
            return calendar.tasks_dest
        case MonthlyTaskWell() as tasks:
            return tasks.calendar_dest
        case (
            FavoritesPage()
            | My100Page()
            | Checkoff365()
            | ProjectsIndex()
            | ProjectsBoard()
            | MeetingIndex()
            | MeetingAgenda()
            | TasksIndex()
            | TasksWeekPage()
            | ReviewIndex()
            | ReviewWeekPage()
            | QuarterGrid()
            | WeekStrip()
            | Schedule()
            | Notes()
            | BujoKey()
            | BujoIndex()
            | FutureLogPage()
            | RapidLogPage()
            | CollectionLeaf()
            | CoverTitle()
            | EngineeringPad()
            | StenoPad()
            | DotGridPad()
            | LinedPad()
        ):
            return None
        case _ as unseen:
            assert_never(unseen)


def _header_chip(page: Page) -> str:
    match page.lead:
        case My100Page() as leaf:
            return f"{leaf.page:02d}" if leaf.pages > 1 else ""
        case ProjectsBoard() as board:
            return f"{board.number:02d}" if board.number else ""
        case MeetingAgenda() as agenda:
            return f"{agenda.number:02d}" if agenda.number else ""
        case TasksWeekPage() as week:
            return f"W{week.iso_week:02d}"
        case ReviewWeekPage() as week:
            return f"W{week.iso_week:02d}"
        case CollectionLeaf() as leaf:
            return f"{leaf.number:02d}"
        case (
            AnnualGrid()
            | FavoritesPage()
            | Checkoff365()
            | ProjectsIndex()
            | MeetingIndex()
            | TasksIndex()
            | ReviewIndex()
            | QuarterGrid()
            | MonthGrid()
            | HabitGrid()
            | WeekStrip()
            | Schedule()
            | Notes()
            | BujoKey()
            | BujoIndex()
            | FutureLogPage()
            | MonthlyCalendarList()
            | MonthlyTaskWell()
            | RapidLogPage()
            | CoverTitle()
            | EngineeringPad()
            | StenoPad()
            | DotGridPad()
            | LinedPad()
        ):
            return ""
        case _ as unseen:
            assert_never(unseen)


def _header_chip_dest(page: Page) -> str | None:
    match page.lead:
        case My100Page() as leaf:
            return leaf.index_dest if leaf.pages > 1 else None
        case ProjectsBoard() as board:
            return board.index_dest or None
        case MeetingAgenda() as agenda:
            return agenda.index_dest or None
        case TasksWeekPage() as week:
            return week.index_dest or None
        case ReviewWeekPage() as week:
            return week.index_dest or None
        case CollectionLeaf() as leaf:
            return leaf.index_dest or None
        case (
            AnnualGrid()
            | FavoritesPage()
            | Checkoff365()
            | ProjectsIndex()
            | MeetingIndex()
            | TasksIndex()
            | ReviewIndex()
            | QuarterGrid()
            | MonthGrid()
            | HabitGrid()
            | WeekStrip()
            | Schedule()
            | Notes()
            | BujoKey()
            | BujoIndex()
            | FutureLogPage()
            | MonthlyCalendarList()
            | MonthlyTaskWell()
            | RapidLogPage()
            | CoverTitle()
            | EngineeringPad()
            | StenoPad()
            | DotGridPad()
            | LinedPad()
        ):
            return None
        case _ as unseen:
            assert_never(unseen)


def _one[T](page: Page, typ: type[T]) -> T:
    for item in page.components:
        if isinstance(item, typ):
            return item
    raise TypeError(f"{page.kind} page missing {typ.__name__}")
