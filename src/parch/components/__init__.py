from parch.components.annual import AnnualGrid, AnnualMonth
from parch.components.bujo import (
    BujoIndex,
    BujoIndexRow,
    BujoKey,
    BujoKeySymbol,
    CalendarDayRow,
    CollectionLeaf,
    FutureLogBand,
    FutureLogPage,
    MonthlyCalendarList,
    MonthlyTaskWell,
    RapidLogPage,
)
from parch.components.checkoff import Checkoff365
from parch.components.cover import CoverTitle
from parch.components.dotgrid import DotGridPad
from parch.components.engineering import EngineeringFace, EngineeringPad
from parch.components.favorites import FavoritesPage
from parch.components.habit import HabitGrid
from parch.components.lined import LinedPad
from parch.components.meeting import MeetingAgenda, MeetingIndex, MeetingSlot
from parch.components.month_grid import MonthCell, MonthGrid, MonthWeek
from parch.components.my_100 import My100Page
from parch.components.notes import Notes
from parch.components.perspective import PerspectivePad
from parch.components.priorities import Priorities
from parch.components.projects import ProjectsBoard, ProjectsIndex, ProjectTicket
from parch.components.quarter import QuarterGrid
from parch.components.review import (
    ReviewDay,
    ReviewIndex,
    ReviewMonthBand,
    ReviewWeek,
    ReviewWeekPage,
)
from parch.components.schedule import Schedule
from parch.components.steno import StenoPad
from parch.components.tasks import TasksIndex, TasksMonthBand, TasksWeekPage, TaskWeek
from parch.components.week import WeekDay, WeekStrip

type Component = (
    AnnualGrid
    | AnnualMonth
    | BujoIndex
    | Checkoff365
    | BujoKey
    | CollectionLeaf
    | CoverTitle
    | DotGridPad
    | EngineeringPad
    | FavoritesPage
    | FutureLogPage
    | HabitGrid
    | LinedPad
    | PerspectivePad
    | MonthlyCalendarList
    | MonthlyTaskWell
    | RapidLogPage
    | MeetingAgenda
    | MeetingIndex
    | MeetingSlot
    | MonthGrid
    | My100Page
    | Notes
    | Priorities
    | ProjectTicket
    | ProjectsBoard
    | ProjectsIndex
    | QuarterGrid
    | ReviewDay
    | ReviewIndex
    | ReviewMonthBand
    | ReviewWeek
    | ReviewWeekPage
    | Schedule
    | StenoPad
    | TaskWeek
    | TasksIndex
    | TasksMonthBand
    | TasksWeekPage
    | WeekStrip
)

# Page-lead unions. Layout matches these — not a PageKind string list.
# Nested Component members (AnnualMonth, tickets, bands, …) never lead.
# New pad: add the type here + a match arm (and to Component if new).
type ChromeComponent = (
    CoverTitle | EngineeringPad | StenoPad | DotGridPad | LinedPad | PerspectivePad
)

type WellComponent = (
    AnnualGrid
    | FavoritesPage
    | My100Page
    | Checkoff365
    | ProjectsIndex
    | ProjectsBoard
    | MeetingIndex
    | MeetingAgenda
    | TasksIndex
    | TasksWeekPage
    | ReviewIndex
    | ReviewWeekPage
    | QuarterGrid
    | MonthGrid
    | HabitGrid
    | WeekStrip
    | Schedule
    | Notes
    | BujoKey
    | BujoIndex
    | FutureLogPage
    | MonthlyCalendarList
    | MonthlyTaskWell
    | RapidLogPage
    | CollectionLeaf
)

type PageComponent = ChromeComponent | WellComponent


def as_page_component(item: Component) -> PageComponent:
    """Narrow a Component to a page lead. Nested members are not leads."""
    match item:
        case (
            CoverTitle()
            | EngineeringPad()
            | StenoPad()
            | DotGridPad()
            | LinedPad()
            | PerspectivePad()
            | AnnualGrid()
            | FavoritesPage()
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
            | CollectionLeaf()
        ) as lead:
            return lead
        case _:
            raise TypeError(f"{type(item).__name__} is not a page component")


__all__ = [
    "AnnualGrid",
    "AnnualMonth",
    "BujoIndex",
    "Checkoff365",
    "BujoIndexRow",
    "BujoKey",
    "BujoKeySymbol",
    "CalendarDayRow",
    "CollectionLeaf",
    "ChromeComponent",
    "Component",
    "CoverTitle",
    "PageComponent",
    "WellComponent",
    "as_page_component",
    "DotGridPad",
    "FutureLogBand",
    "FutureLogPage",
    "MonthlyCalendarList",
    "MonthlyTaskWell",
    "RapidLogPage",
    "EngineeringFace",
    "EngineeringPad",
    "FavoritesPage",
    "HabitGrid",
    "LinedPad",
    "MeetingAgenda",
    "MeetingIndex",
    "MeetingSlot",
    "MonthCell",
    "MonthGrid",
    "MonthWeek",
    "My100Page",
    "Notes",
    "PerspectivePad",
    "Priorities",
    "ProjectTicket",
    "ProjectsBoard",
    "ProjectsIndex",
    "QuarterGrid",
    "ReviewDay",
    "ReviewIndex",
    "ReviewMonthBand",
    "ReviewWeek",
    "ReviewWeekPage",
    "Schedule",
    "StenoPad",
    "TaskWeek",
    "TasksIndex",
    "TasksMonthBand",
    "TasksWeekPage",
    "WeekDay",
    "WeekStrip",
]
