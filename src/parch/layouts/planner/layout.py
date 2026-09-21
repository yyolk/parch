"""Planner layout: device chrome + seat, then painters."""

from typing import assert_never

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
    strip_items,
    well_rect,
)
from parch.plotter.protocol import Plotter
from parch.sections.page import Page
from parch.sections.seating import seating_view

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
        view = seating_view(page.components, page.dest)
        match view.frame:
            case "bleed":
                _ink(page, plotter, device, self.ramp, None)
            case "chrome":
                overlay = view.overlay
                paint_header(
                    plotter,
                    device,
                    page.title,
                    overlay.meta,
                    overlay.meta_dest,
                    ramp=self.ramp,
                    chip=overlay.chip,
                    chip_dest=overlay.chip_dest,
                )
                paint_nav(
                    plotter,
                    device,
                    strip_items(page),
                    view.strip,
                    ramp=self.ramp,
                )
                _ink(page, plotter, device, self.ramp, well_rect(device))
            case _:
                assert_never(view.frame)


def _ink(
    page: Page,
    plotter: Plotter,
    device: Device,
    ramp: TypeRamp,
    well: Rect | None,
) -> None:
    """Paint the seating. A new tuple shape fails ``assert_never``."""
    match page.components:
        case (CoverTitle() as cover,):
            paint_cover(plotter, device, cover, ramp=ramp)
        case (EngineeringPad() as pad,):
            paint_engineering_pad(plotter, device, pad, ramp=ramp)
        case (StenoPad() as pad,):
            paint_steno_pad(plotter, device, pad, ramp=ramp)
        case (DotGridPad() as pad,):
            paint_dotgrid_page(plotter, device, pad, ramp=ramp)
        case (LinedPad() as pad,):
            paint_lined_page(plotter, device, pad, ramp=ramp)
        case (AnnualGrid() as grid,):
            assert well is not None
            paint_annual(plotter, well, grid, ramp=ramp)
        case (FavoritesPage() as fav,):
            assert well is not None
            paint_favorites(plotter, well, fav, ramp=ramp)
        case (My100Page() as leaf,):
            assert well is not None
            paint_my_100(plotter, well, leaf, ramp=ramp)
        case (Checkoff365() as sheet,):
            assert well is not None
            paint_checkoff_365(plotter, well, sheet, ramp=ramp)
        case (ProjectsIndex() as index,):
            assert well is not None
            paint_projects_index(plotter, well, index, ramp=ramp)
        case (ProjectsBoard() as board,):
            assert well is not None
            paint_project(plotter, well, board, ramp=ramp)
        case (MeetingIndex() as index,):
            assert well is not None
            paint_meetings_index(plotter, well, index, ramp=ramp)
        case (MeetingAgenda() as agenda,):
            assert well is not None
            paint_meeting(plotter, well, agenda, ramp=ramp)
        case (TasksIndex() as index,):
            assert well is not None
            paint_tasks_index(plotter, well, index, ramp=ramp)
        case (TasksWeekPage() as week,):
            assert well is not None
            paint_task(plotter, well, week, ramp=ramp)
        case (ReviewIndex() as index,):
            assert well is not None
            paint_review_index(plotter, well, index, ramp=ramp)
        case (ReviewWeekPage() as week,):
            assert well is not None
            paint_review(plotter, well, week, ramp=ramp)
        case (QuarterGrid() as grid,):
            assert well is not None
            paint_quarter(plotter, well, grid, ramp=ramp)
        case (MonthGrid() as grid,):
            assert well is not None
            paint_month_grid(plotter, well, grid, ramp=ramp)
        case (HabitGrid() as grid,):
            assert well is not None
            paint_habit_grid(plotter, well, grid, ramp=ramp)
        case (WeekStrip() as week,):
            assert well is not None
            paint_week(plotter, well, week, ramp=ramp)
        case (
            Schedule() as schedule,
            Notes() as notes,
            Priorities() as priorities,
            AnnualMonth() as mini,
        ):
            assert well is not None
            paint_daily(
                plotter,
                well,
                schedule,
                mini,
                priorities,
                notes,
                ramp=ramp,
            )
        case (Notes() as notes,):
            assert well is not None
            paint_notes(plotter, well, notes, ramp=ramp)
        case (BujoKey() as key,):
            assert well is not None
            paint_bujo_key(plotter, well, key, ramp=ramp)
        case (BujoIndex() as index,):
            assert well is not None
            paint_bujo_index(plotter, well, index, ramp=ramp)
        case (FutureLogPage() as future,):
            assert well is not None
            paint_future_log(plotter, well, future, ramp=ramp)
        case (MonthlyCalendarList() as cal,):
            assert well is not None
            paint_monthly_calendar_list(plotter, well, cal, ramp=ramp)
        case (MonthlyTaskWell() as tasks,):
            assert well is not None
            paint_monthly_task_well(plotter, well, tasks, ramp=ramp)
        case (RapidLogPage() as log,):
            assert well is not None
            paint_rapid_log(plotter, well, log, ramp=ramp)
        case (CollectionLeaf() as leaf,):
            assert well is not None
            paint_collection(plotter, well, leaf, ramp=ramp)
        case _:
            assert_never(page.components)
