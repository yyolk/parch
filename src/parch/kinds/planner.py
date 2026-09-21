"""Planner family: year-book pages. Closed union is ``PlannerKind``."""

from typing import Literal, TypeIs, assert_never, cast

from parch.calendar import quarter_of, short_date_range
from parch.components import (
    AnnualGrid,
    AnnualMonth,
    Checkoff365,
    FavoritesPage,
    HabitGrid,
    MeetingAgenda,
    MeetingIndex,
    MonthGrid,
    My100Page,
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
from parch.devices.registry import Device
from parch.fonts.ramp import TypeRamp
from parch.kinds.members import literal_members
from parch.kinds.seat import PageLike, one
from parch.plotter.protocol import Plotter

type PlannerKind = Literal[
    "annual",
    "favorites",
    "my_100",
    "checkoff_365",
    "projects_index",
    "project",
    "meetings_index",
    "meeting",
    "tasks_index",
    "task",
    "review_index",
    "review",
    "quarter",
    "month",
    "habits",
    "weekly",
    "daily",
    "daily_notes",
]

PLANNER_KINDS: frozenset[PlannerKind] = cast(
    frozenset[PlannerKind], literal_members(PlannerKind)
)


def is_planner_kind(kind: str) -> TypeIs[PlannerKind]:
    """True when ``kind`` belongs to the planner family."""
    return kind in PLANNER_KINDS


def exhaust_planner_kind(kind: PlannerKind) -> PlannerKind:
    """Closed planner identity. A new member needs a case here."""
    match kind:
        case (
            "annual"
            | "favorites"
            | "my_100"
            | "checkoff_365"
            | "projects_index"
            | "project"
            | "meetings_index"
            | "meeting"
            | "tasks_index"
            | "task"
            | "review_index"
            | "review"
            | "quarter"
            | "month"
            | "habits"
            | "weekly"
            | "daily"
            | "daily_notes"
        ):
            return kind
        case _:
            assert_never(kind)


def planner_strip_active(kind: PlannerKind) -> str:
    """Active strip label for a planner kind."""
    match kind:
        case "annual":
            return "Year"
        case "favorites":
            return "Fav"
        case "my_100":
            return "100"
        case "checkoff_365":
            return "365"
        case "quarter":
            return "Quar"
        case "month":
            return "Mon"
        case "weekly":
            return "Week"
        case "daily":
            return "Day"
        case "daily_notes":
            return "Notes"
        case "habits":
            return "Habit"
        case "projects_index" | "project":
            return "Proj"
        case "meetings_index" | "meeting":
            return "Meet"
        case "tasks_index" | "task":
            return "Task"
        case "review_index" | "review":
            return "Rev"
        case _:
            assert_never(kind)


def planner_header_meta(page: PageLike, kind: PlannerKind) -> str:
    """Header meta for a planner kind."""
    match kind:
        case "annual":
            return "Q1–Q4"
        case "favorites":
            return str(one(page, FavoritesPage).year)
        case "my_100":
            return str(one(page, My100Page).year)
        case "checkoff_365":
            return str(one(page, Checkoff365).year)
        case "projects_index":
            return str(one(page, ProjectsIndex).year)
        case "project":
            return str(one(page, ProjectsBoard).year)
        case "meetings_index":
            return str(one(page, MeetingIndex).year)
        case "meeting":
            return str(one(page, MeetingAgenda).year)
        case "tasks_index":
            return f"Q{one(page, TasksIndex).quarter}"
        case "task":
            return str(one(page, TasksWeekPage).year)
        case "review_index":
            return str(one(page, ReviewIndex).year)
        case "review":
            return str(one(page, ReviewWeekPage).year)
        case "quarter":
            return ""
        case "month":
            return f"Q{quarter_of(one(page, MonthGrid).month)}"
        case "habits":
            grid = one(page, HabitGrid)
            return f"Q{quarter_of(grid.month)}" if grid.quarter_dest else ""
        case "weekly":
            week = one(page, WeekStrip)
            return short_date_range(week.monday, week.sunday)
        case "daily":
            return page.dest[:4]
        case "daily_notes":
            label = one(page, Notes).label
            return label.rsplit(" ", 1)[-1] if " " in label else page.dest[:4]
        case _:
            assert_never(kind)


def planner_header_meta_dest(page: PageLike, kind: PlannerKind) -> str | None:
    """Header meta link for a planner kind."""
    match kind:
        case "annual":
            return one(page, AnnualGrid).quarter_dest
        case "month":
            return one(page, MonthGrid).quarter_dest
        case "habits":
            return one(page, HabitGrid).quarter_dest
        case (
            "favorites"
            | "my_100"
            | "checkoff_365"
            | "projects_index"
            | "project"
            | "meetings_index"
            | "meeting"
            | "tasks_index"
            | "task"
            | "review_index"
            | "review"
            | "quarter"
            | "weekly"
            | "daily"
            | "daily_notes"
        ):
            return None
        case _:
            assert_never(kind)


def planner_header_chip(page: PageLike, kind: PlannerKind) -> str:
    """Right-hand header chip for a planner kind."""
    match kind:
        case "my_100":
            leaf = one(page, My100Page)
            return f"{leaf.page:02d}" if leaf.pages > 1 else ""
        case "project":
            number = one(page, ProjectsBoard).number
            return f"{number:02d}" if number else ""
        case "meeting":
            number = one(page, MeetingAgenda).number
            return f"{number:02d}" if number else ""
        case "task":
            week = one(page, TasksWeekPage)
            return f"W{week.iso_week:02d}"
        case "review":
            week = one(page, ReviewWeekPage)
            return f"W{week.iso_week:02d}"
        case (
            "annual"
            | "favorites"
            | "checkoff_365"
            | "projects_index"
            | "meetings_index"
            | "tasks_index"
            | "review_index"
            | "quarter"
            | "month"
            | "habits"
            | "weekly"
            | "daily"
            | "daily_notes"
        ):
            return ""
        case _:
            assert_never(kind)


def planner_header_chip_dest(page: PageLike, kind: PlannerKind) -> str | None:
    """Header chip link for a planner kind."""
    match kind:
        case "my_100":
            leaf = one(page, My100Page)
            return leaf.index_dest if leaf.pages > 1 else None
        case "project":
            return one(page, ProjectsBoard).index_dest or None
        case "meeting":
            return one(page, MeetingAgenda).index_dest or None
        case "task":
            return one(page, TasksWeekPage).index_dest or None
        case "review":
            return one(page, ReviewWeekPage).index_dest or None
        case (
            "annual"
            | "favorites"
            | "checkoff_365"
            | "projects_index"
            | "meetings_index"
            | "tasks_index"
            | "review_index"
            | "quarter"
            | "month"
            | "habits"
            | "weekly"
            | "daily"
            | "daily_notes"
        ):
            return None
        case _:
            assert_never(kind)


def planner_strip_dests(
    page: PageLike, kind: PlannerKind, dests: dict[str, str]
) -> None:
    """Planner pages claim their own strip slot."""
    match kind:
        case "annual":
            dests["Year"] = page.dest
        case "favorites":
            dests["Fav"] = page.dest
        case "checkoff_365":
            dests["365"] = page.dest
        case "quarter":
            dests["Quar"] = page.dest
        case "month":
            dests["Mon"] = page.dest
        case "habits":
            dests["Habit"] = page.dest
        case "projects_index":
            dests["Proj"] = page.dest
        case "meetings_index":
            dests["Meet"] = page.dest
        case "tasks_index":
            dests["Task"] = page.dest
        case "review_index":
            dests["Rev"] = page.dest
        case "weekly":
            dests["Week"] = page.dest
        case "daily":
            dests["Day"] = page.dest
        case "daily_notes":
            dests["Notes"] = page.dest
            dests["Day"] = page.dest.rsplit("-notes-", 1)[0]
        case "my_100" | "project" | "meeting" | "task" | "review":
            pass
        case _:
            assert_never(kind)


def paint_planner(
    page: PageLike, plotter: Plotter, device: Device, ramp: TypeRamp, kind: PlannerKind
) -> None:
    """Header, strip, and well for a planner kind."""
    from parch.layouts.planner.painters import (
        paint_annual,
        paint_checkoff_365,
        paint_daily,
        paint_favorites,
        paint_habit_grid,
        paint_header,
        paint_meeting,
        paint_meetings_index,
        paint_month_grid,
        paint_my_100,
        paint_nav,
        paint_notes,
        paint_project,
        paint_projects_index,
        paint_quarter,
        paint_review,
        paint_review_index,
        paint_task,
        paint_tasks_index,
        paint_week,
        strip_items,
        well_rect,
    )

    paint_header(
        plotter,
        device,
        page.title,
        planner_header_meta(page, kind),
        planner_header_meta_dest(page, kind),
        ramp=ramp,
        chip=planner_header_chip(page, kind),
        chip_dest=planner_header_chip_dest(page, kind),
    )
    paint_nav(
        plotter,
        device,
        strip_items(page),
        planner_strip_active(kind),
        ramp=ramp,
    )
    well = well_rect(device)
    match kind:
        case "annual":
            paint_annual(plotter, well, one(page, AnnualGrid), ramp=ramp)
        case "favorites":
            paint_favorites(plotter, well, one(page, FavoritesPage), ramp=ramp)
        case "my_100":
            paint_my_100(plotter, well, one(page, My100Page), ramp=ramp)
        case "checkoff_365":
            paint_checkoff_365(plotter, well, one(page, Checkoff365), ramp=ramp)
        case "projects_index":
            paint_projects_index(plotter, well, one(page, ProjectsIndex), ramp=ramp)
        case "project":
            paint_project(plotter, well, one(page, ProjectsBoard), ramp=ramp)
        case "meetings_index":
            paint_meetings_index(plotter, well, one(page, MeetingIndex), ramp=ramp)
        case "meeting":
            paint_meeting(plotter, well, one(page, MeetingAgenda), ramp=ramp)
        case "tasks_index":
            paint_tasks_index(plotter, well, one(page, TasksIndex), ramp=ramp)
        case "task":
            paint_task(plotter, well, one(page, TasksWeekPage), ramp=ramp)
        case "review_index":
            paint_review_index(plotter, well, one(page, ReviewIndex), ramp=ramp)
        case "review":
            paint_review(plotter, well, one(page, ReviewWeekPage), ramp=ramp)
        case "quarter":
            paint_quarter(plotter, well, one(page, QuarterGrid), ramp=ramp)
        case "month":
            paint_month_grid(plotter, well, one(page, MonthGrid), ramp=ramp)
        case "habits":
            paint_habit_grid(plotter, well, one(page, HabitGrid), ramp=ramp)
        case "weekly":
            paint_week(plotter, well, one(page, WeekStrip), ramp=ramp)
        case "daily":
            paint_daily(
                plotter,
                well,
                one(page, Schedule),
                one(page, AnnualMonth),
                one(page, Priorities),
                one(page, Notes),
                ramp=ramp,
            )
        case "daily_notes":
            paint_notes(plotter, well, one(page, Notes), ramp=ramp)
        case _:
            assert_never(kind)
