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
from parch.sections.page import (
    AnnualPage,
    BujoIndexPage,
    BujoKeyPage,
    Checkoff365Page,
    CollectionPage,
    CoverPage,
    DailyNotesPage,
    DailyPage,
    DotgridPage,
    EngineeringBackPage,
    EngineeringFrontPage,
    FavoritesHubPage,
    FutureLogHubPage,
    HabitsPage,
    HeaderPage,
    MeetingPage,
    MeetingsIndexPage,
    MonthlyLogPage,
    MonthlyTasksPage,
    MonthPage,
    My100HubPage,
    Page,
    ProjectPage,
    ProjectsIndexPage,
    QuarterPage,
    RapidLogHubPage,
    ReviewIndexPage,
    ReviewPage,
    StenoPadPage,
    TaskPage,
    TasksIndexPage,
    WeeklyPage,
)

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
        match page:
            case CoverPage():
                paint_cover(plotter, device, _one(page, CoverTitle), ramp=self.ramp)
            case EngineeringFrontPage() | EngineeringBackPage():
                paint_engineering_pad(
                    plotter, device, _one(page, EngineeringPad), ramp=self.ramp
                )
            case StenoPadPage():
                paint_steno_pad(plotter, device, _one(page, StenoPad), ramp=self.ramp)
            case DotgridPage():
                paint_dotgrid_page(
                    plotter, device, _one(page, DotGridPad), ramp=self.ramp
                )
            case (
                AnnualPage()
                | FavoritesHubPage()
                | My100HubPage()
                | Checkoff365Page()
                | ProjectsIndexPage()
                | ProjectPage()
                | MeetingsIndexPage()
                | MeetingPage()
                | TasksIndexPage()
                | TaskPage()
                | ReviewIndexPage()
                | ReviewPage()
                | QuarterPage()
                | MonthPage()
                | HabitsPage()
                | WeeklyPage()
                | DailyPage()
                | DailyNotesPage()
                | BujoKeyPage()
                | BujoIndexPage()
                | FutureLogHubPage()
                | MonthlyLogPage()
                | MonthlyTasksPage()
                | RapidLogHubPage()
                | CollectionPage()
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
            case _ as unreachable:
                assert_never(unreachable)

    def _paint_well(self, page: HeaderPage, plotter: Plotter, well: Rect) -> None:
        ramp = self.ramp
        match page:
            case AnnualPage():
                paint_annual(plotter, well, _one(page, AnnualGrid), ramp=ramp)
            case FavoritesHubPage():
                paint_favorites(plotter, well, _one(page, FavoritesPage), ramp=ramp)
            case My100HubPage():
                paint_my_100(plotter, well, _one(page, My100Page), ramp=ramp)
            case Checkoff365Page():
                paint_checkoff_365(plotter, well, _one(page, Checkoff365), ramp=ramp)
            case ProjectsIndexPage():
                paint_projects_index(
                    plotter, well, _one(page, ProjectsIndex), ramp=ramp
                )
            case ProjectPage():
                paint_project(plotter, well, _one(page, ProjectsBoard), ramp=ramp)
            case MeetingsIndexPage():
                paint_meetings_index(plotter, well, _one(page, MeetingIndex), ramp=ramp)
            case MeetingPage():
                paint_meeting(plotter, well, _one(page, MeetingAgenda), ramp=ramp)
            case TasksIndexPage():
                paint_tasks_index(plotter, well, _one(page, TasksIndex), ramp=ramp)
            case TaskPage():
                paint_task(plotter, well, _one(page, TasksWeekPage), ramp=ramp)
            case ReviewIndexPage():
                paint_review_index(plotter, well, _one(page, ReviewIndex), ramp=ramp)
            case ReviewPage():
                paint_review(plotter, well, _one(page, ReviewWeekPage), ramp=ramp)
            case QuarterPage():
                paint_quarter(plotter, well, _one(page, QuarterGrid), ramp=ramp)
            case MonthPage():
                paint_month_grid(plotter, well, _one(page, MonthGrid), ramp=ramp)
            case HabitsPage():
                paint_habit_grid(plotter, well, _one(page, HabitGrid), ramp=ramp)
            case WeeklyPage():
                paint_week(plotter, well, _one(page, WeekStrip), ramp=ramp)
            case DailyPage():
                paint_daily(
                    plotter,
                    well,
                    _one(page, Schedule),
                    _one(page, AnnualMonth),
                    _one(page, Priorities),
                    _one(page, Notes),
                    ramp=ramp,
                )
            case DailyNotesPage():
                paint_notes(plotter, well, _one(page, Notes), ramp=ramp)
            case BujoKeyPage():
                paint_bujo_key(plotter, well, _one(page, BujoKey), ramp=ramp)
            case BujoIndexPage():
                paint_bujo_index(plotter, well, _one(page, BujoIndex), ramp=ramp)
            case FutureLogHubPage():
                paint_future_log(plotter, well, _one(page, FutureLogPage), ramp=ramp)
            case MonthlyLogPage():
                paint_monthly_calendar_list(
                    plotter, well, _one(page, MonthlyCalendarList), ramp=ramp
                )
            case MonthlyTasksPage():
                paint_monthly_task_well(
                    plotter, well, _one(page, MonthlyTaskWell), ramp=ramp
                )
            case RapidLogHubPage():
                paint_rapid_log(plotter, well, _one(page, RapidLogPage), ramp=ramp)
            case CollectionPage():
                paint_collection(plotter, well, _one(page, CollectionLeaf), ramp=ramp)
            case _ as unreachable:
                assert_never(unreachable)


def _header_meta(page: HeaderPage) -> str:
    match page:
        case AnnualPage():
            return "Q1–Q4"
        case FavoritesHubPage():
            return str(_one(page, FavoritesPage).year)
        case My100HubPage():
            return str(_one(page, My100Page).year)
        case Checkoff365Page():
            return str(_one(page, Checkoff365).year)
        case ProjectsIndexPage():
            return str(_one(page, ProjectsIndex).year)
        case ProjectPage():
            return str(_one(page, ProjectsBoard).year)
        case MeetingsIndexPage():
            return str(_one(page, MeetingIndex).year)
        case MeetingPage():
            return str(_one(page, MeetingAgenda).year)
        case TasksIndexPage():
            return f"Q{_one(page, TasksIndex).quarter}"
        case TaskPage():
            return str(_one(page, TasksWeekPage).year)
        case ReviewIndexPage():
            return str(_one(page, ReviewIndex).year)
        case ReviewPage():
            return str(_one(page, ReviewWeekPage).year)
        case QuarterPage():
            return ""
        case MonthPage():
            month = _one(page, MonthGrid).month
            return f"Q{quarter_of(month)}"
        case HabitsPage():
            grid = _one(page, HabitGrid)
            return f"Q{quarter_of(grid.month)}" if grid.quarter_dest else ""
        case BujoKeyPage():
            return page.dest.rsplit("-", 1)[-1]
        case BujoIndexPage():
            index = _one(page, BujoIndex)
            return f"{index.page}/{index.pages}"
        case FutureLogHubPage():
            future = _one(page, FutureLogPage)
            return f"{future.page}/{future.pages}"
        case MonthlyLogPage():
            return "Tasks"
        case MonthlyTasksPage():
            return _one(page, MonthlyTaskWell).month_name[:3]
        case RapidLogHubPage():
            return page.dest[:4]
        case CollectionPage():
            return str(_one(page, CollectionLeaf).year)
        case WeeklyPage():
            week = _one(page, WeekStrip)
            return short_date_range(week.monday, week.sunday)
        case DailyPage():
            return page.dest[:4]
        case DailyNotesPage():
            label = _one(page, Notes).label
            return label.rsplit(" ", 1)[-1] if " " in label else page.dest[:4]
        case _ as unreachable:
            assert_never(unreachable)


def _header_meta_dest(page: HeaderPage) -> str | None:
    match page:
        case AnnualPage():
            return _one(page, AnnualGrid).quarter_dest
        case MonthPage():
            return _one(page, MonthGrid).quarter_dest
        case HabitsPage():
            return _one(page, HabitGrid).quarter_dest
        case MonthlyLogPage():
            return _one(page, MonthlyCalendarList).tasks_dest
        case MonthlyTasksPage():
            return _one(page, MonthlyTaskWell).calendar_dest
        case (
            FavoritesHubPage()
            | My100HubPage()
            | Checkoff365Page()
            | ProjectsIndexPage()
            | ProjectPage()
            | MeetingsIndexPage()
            | MeetingPage()
            | TasksIndexPage()
            | TaskPage()
            | ReviewIndexPage()
            | ReviewPage()
            | QuarterPage()
            | WeeklyPage()
            | DailyPage()
            | DailyNotesPage()
            | BujoKeyPage()
            | BujoIndexPage()
            | FutureLogHubPage()
            | RapidLogHubPage()
            | CollectionPage()
        ):
            return None
        case _ as unreachable:
            assert_never(unreachable)


def _header_chip(page: HeaderPage) -> str:
    match page:
        case My100HubPage():
            leaf = _one(page, My100Page)
            return f"{leaf.page:02d}" if leaf.pages > 1 else ""
        case ProjectPage():
            number = _one(page, ProjectsBoard).number
            return f"{number:02d}" if number else ""
        case MeetingPage():
            number = _one(page, MeetingAgenda).number
            return f"{number:02d}" if number else ""
        case TaskPage():
            week = _one(page, TasksWeekPage)
            return f"W{week.iso_week:02d}"
        case ReviewPage():
            week = _one(page, ReviewWeekPage)
            return f"W{week.iso_week:02d}"
        case CollectionPage():
            number = _one(page, CollectionLeaf).number
            return f"{number:02d}"
        case (
            AnnualPage()
            | FavoritesHubPage()
            | Checkoff365Page()
            | ProjectsIndexPage()
            | MeetingsIndexPage()
            | TasksIndexPage()
            | ReviewIndexPage()
            | QuarterPage()
            | MonthPage()
            | HabitsPage()
            | WeeklyPage()
            | DailyPage()
            | DailyNotesPage()
            | BujoKeyPage()
            | BujoIndexPage()
            | FutureLogHubPage()
            | MonthlyLogPage()
            | MonthlyTasksPage()
            | RapidLogHubPage()
        ):
            return ""
        case _ as unreachable:
            assert_never(unreachable)


def _header_chip_dest(page: HeaderPage) -> str | None:
    match page:
        case My100HubPage():
            leaf = _one(page, My100Page)
            return leaf.index_dest if leaf.pages > 1 else None
        case ProjectPage():
            return _one(page, ProjectsBoard).index_dest or None
        case MeetingPage():
            return _one(page, MeetingAgenda).index_dest or None
        case TaskPage():
            return _one(page, TasksWeekPage).index_dest or None
        case ReviewPage():
            return _one(page, ReviewWeekPage).index_dest or None
        case CollectionPage():
            return _one(page, CollectionLeaf).index_dest or None
        case (
            AnnualPage()
            | FavoritesHubPage()
            | Checkoff365Page()
            | ProjectsIndexPage()
            | MeetingsIndexPage()
            | TasksIndexPage()
            | ReviewIndexPage()
            | QuarterPage()
            | MonthPage()
            | HabitsPage()
            | WeeklyPage()
            | DailyPage()
            | DailyNotesPage()
            | BujoKeyPage()
            | BujoIndexPage()
            | FutureLogHubPage()
            | MonthlyLogPage()
            | MonthlyTasksPage()
            | RapidLogHubPage()
        ):
            return None
        case _ as unreachable:
            assert_never(unreachable)


def _one[T](page: Page, typ: type[T]) -> T:
    for item in page.components:
        if isinstance(item, typ):
            return item
    raise TypeError(f"{page.kind} page missing {typ.__name__}")
