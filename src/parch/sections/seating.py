"""Component tuple is the closed set. The kind string is a view of it."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, assert_never

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
from parch.sections.kind import PageKind

type OutlinePolicy = Literal["run", "each", "skip"]
type Frame = Literal["bleed", "chrome"]
type Pin = Callable[[dict[str, str]], None]
type Seating = (
    tuple[CoverTitle]
    | tuple[EngineeringPad]
    | tuple[StenoPad]
    | tuple[DotGridPad]
    | tuple[LinedPad]
    | tuple[AnnualGrid]
    | tuple[FavoritesPage]
    | tuple[My100Page]
    | tuple[Checkoff365]
    | tuple[ProjectsIndex]
    | tuple[ProjectsBoard]
    | tuple[MeetingIndex]
    | tuple[MeetingAgenda]
    | tuple[TasksIndex]
    | tuple[TasksWeekPage]
    | tuple[ReviewIndex]
    | tuple[ReviewWeekPage]
    | tuple[QuarterGrid]
    | tuple[MonthGrid]
    | tuple[HabitGrid]
    | tuple[WeekStrip]
    | tuple[Schedule, Notes, Priorities, AnnualMonth]
    | tuple[Notes]
    | tuple[BujoKey]
    | tuple[BujoIndex]
    | tuple[FutureLogPage]
    | tuple[MonthlyCalendarList]
    | tuple[MonthlyTaskWell]
    | tuple[RapidLogPage]
    | tuple[CollectionLeaf]
)


@dataclass(frozen=True, slots=True)
class HeaderOverlay:
    """Header meta, chip, and link dests. Empty chip text hides the chip."""

    meta: str = ""
    meta_dest: str | None = None
    chip: str = ""
    chip_dest: str | None = None


@dataclass(frozen=True, slots=True)
class SeatingView:
    """Label and chrome policy for one seating. Ink is not in here."""

    kind: PageKind
    strip: str
    outline: OutlinePolicy
    frame: Frame
    overlay: HeaderOverlay
    pin: Pin


def seating_view(components: Seating, dest: str) -> SeatingView:
    """Total on ``Seating``. A new tuple shape fails ``assert_never``."""
    match components:
        case (CoverTitle(),):
            return _bleed("cover")
        case (EngineeringPad(face=face),):
            match face:
                case "front":
                    return _bleed("engineering_front")
                case "back":
                    return _bleed("engineering_back")
                case _:
                    assert_never(face)
        case (StenoPad(),):
            return _bleed("steno")
        case (DotGridPad(),):
            return _bleed("dotgrid")
        case (LinedPad(),):
            return _bleed("lined")
        case (AnnualGrid() as grid,):
            return _chrome(
                "annual",
                "Year",
                "run",
                HeaderOverlay("Q1–Q4", grid.quarter_dest),
                _pin("Year", dest),
            )
        case (FavoritesPage() as fav,):
            return _chrome(
                "favorites",
                "Fav",
                "run",
                HeaderOverlay(str(fav.year)),
                _pin("Fav", dest),
            )
        case (My100Page() as leaf,):
            chip = f"{leaf.page:02d}" if leaf.pages > 1 else ""
            chip_dest = leaf.index_dest if leaf.pages > 1 else None
            return _chrome(
                "my_100",
                "100",
                "run",
                HeaderOverlay(str(leaf.year), chip=chip, chip_dest=chip_dest),
                _nop,
            )
        case (Checkoff365() as sheet,):
            return _chrome(
                "checkoff_365",
                "365",
                "run",
                HeaderOverlay(str(sheet.year)),
                _pin("365", dest),
            )
        case (ProjectsIndex() as index,):
            return _chrome(
                "projects_index",
                "Proj",
                "run",
                HeaderOverlay(str(index.year)),
                _pin("Proj", dest),
            )
        case (ProjectsBoard() as board,):
            chip = f"{board.number:02d}" if board.number else ""
            return _chrome(
                "project",
                "Proj",
                "skip",
                HeaderOverlay(
                    str(board.year), chip=chip, chip_dest=board.index_dest or None
                ),
                _nop,
            )
        case (MeetingIndex() as index,):
            return _chrome(
                "meetings_index",
                "Meet",
                "run",
                HeaderOverlay(str(index.year)),
                _pin("Meet", dest),
            )
        case (MeetingAgenda() as agenda,):
            chip = f"{agenda.number:02d}" if agenda.number else ""
            return _chrome(
                "meeting",
                "Meet",
                "skip",
                HeaderOverlay(
                    str(agenda.year), chip=chip, chip_dest=agenda.index_dest or None
                ),
                _nop,
            )
        case (TasksIndex() as index,):
            return _chrome(
                "tasks_index",
                "Task",
                "run",
                HeaderOverlay(f"Q{index.quarter}"),
                _pin("Task", dest),
            )
        case (TasksWeekPage() as week,):
            return _chrome(
                "task",
                "Task",
                "skip",
                HeaderOverlay(
                    str(week.year),
                    chip=f"W{week.iso_week:02d}",
                    chip_dest=week.index_dest or None,
                ),
                _nop,
            )
        case (ReviewIndex() as index,):
            return _chrome(
                "review_index",
                "Rev",
                "run",
                HeaderOverlay(str(index.year)),
                _pin("Rev", dest),
            )
        case (ReviewWeekPage() as week,):
            return _chrome(
                "review",
                "Rev",
                "skip",
                HeaderOverlay(
                    str(week.year),
                    chip=f"W{week.iso_week:02d}",
                    chip_dest=week.index_dest or None,
                ),
                _nop,
            )
        case (QuarterGrid(),):
            return _chrome(
                "quarter", "Quar", "each", HeaderOverlay(), _pin("Quar", dest)
            )
        case (MonthGrid() as grid,):
            return _chrome(
                "month",
                "Mon",
                "each",
                HeaderOverlay(f"Q{quarter_of(grid.month)}", grid.quarter_dest),
                _pin("Mon", dest),
            )
        case (HabitGrid() as grid,):
            meta = f"Q{quarter_of(grid.month)}" if grid.quarter_dest else ""
            return _chrome(
                "habits",
                "Habit",
                "skip",
                HeaderOverlay(meta, grid.quarter_dest),
                _pin("Habit", dest),
            )
        case (WeekStrip() as week,):
            return _chrome(
                "weekly",
                "Week",
                "skip",
                HeaderOverlay(short_date_range(week.monday, week.sunday)),
                _pin("Week", dest),
            )
        case (Schedule(), Notes(), Priorities(), AnnualMonth()):
            return _chrome(
                "daily", "Day", "skip", HeaderOverlay(dest[:4]), _pin("Day", dest)
            )
        case (Notes() as notes,):
            label = notes.label
            meta = label.rsplit(" ", 1)[-1] if " " in label else dest[:4]
            return _chrome(
                "daily_notes",
                "Notes",
                "skip",
                HeaderOverlay(meta),
                _pin_notes(dest),
            )
        case (BujoKey(),):
            return _chrome(
                "bujo_key",
                "Key",
                "run",
                HeaderOverlay(dest.rsplit("-", 1)[-1]),
                _pin("Key", dest),
            )
        case (BujoIndex() as index,):
            return _chrome(
                "bujo_index",
                "Idx",
                "run",
                HeaderOverlay(f"{index.page}/{index.pages}"),
                _pin("Idx", dest),
            )
        case (FutureLogPage() as future,):
            return _chrome(
                "future_log",
                "Fut",
                "run",
                HeaderOverlay(f"{future.page}/{future.pages}"),
                _pin("Fut", dest),
            )
        case (MonthlyCalendarList() as cal,):
            return _chrome(
                "monthly_log",
                "Mon",
                "each",
                HeaderOverlay("Tasks", cal.tasks_dest),
                _pin("Mon", dest),
            )
        case (MonthlyTaskWell() as tasks,):
            return _chrome(
                "monthly_tasks",
                "Mon",
                "skip",
                HeaderOverlay(tasks.month_name[:3], tasks.calendar_dest),
                _pin_tasks(dest),
            )
        case (RapidLogPage(),):
            return _chrome(
                "rapid_log", "Day", "skip", HeaderOverlay(dest[:4]), _pin("Day", dest)
            )
        case (CollectionLeaf() as leaf,):
            return _chrome(
                "collection",
                "Col",
                "run",
                HeaderOverlay(
                    str(leaf.year),
                    chip=f"{leaf.number:02d}",
                    chip_dest=leaf.index_dest or None,
                ),
                _pin("Col", dest),
            )
        case _:
            assert_never(components)


def _bleed(kind: PageKind) -> SeatingView:
    return SeatingView(kind, "", "skip", "bleed", HeaderOverlay(), _nop)


def _chrome(
    kind: PageKind,
    strip: str,
    outline: OutlinePolicy,
    overlay: HeaderOverlay,
    pin: Pin,
) -> SeatingView:
    return SeatingView(kind, strip, outline, "chrome", overlay, pin)


def _pin(label: str, dest: str) -> Pin:
    def pin(dests: dict[str, str]) -> None:
        dests[label] = dest

    return pin


def _pin_notes(dest: str) -> Pin:
    def pin(dests: dict[str, str]) -> None:
        dests["Notes"] = dest
        dests["Day"] = dest.rsplit("-notes-", 1)[0]

    return pin


def _pin_tasks(dest: str) -> Pin:
    def pin(dests: dict[str, str]) -> None:
        dests["Mon"] = dests.get("Mon", dest)

    return pin


def _nop(_dests: dict[str, str]) -> None:
    """Leave strip dests as nav parsing left them."""
