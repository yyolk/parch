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
from parch.components.dot_grid import DotGridSheet
from parch.components.engineering import EngineeringFace, EngineeringPad
from parch.components.favorites import FavoritesPage
from parch.components.habit import HabitGrid
from parch.components.meeting import MeetingAgenda, MeetingIndex, MeetingSlot
from parch.components.month_grid import MonthCell, MonthGrid, MonthWeek
from parch.components.my_100 import My100Page
from parch.components.notes import Notes
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
    | DotGridSheet
    | EngineeringPad
    | FavoritesPage
    | FutureLogPage
    | HabitGrid
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
    "Component",
    "CoverTitle",
    "DotGridSheet",
    "FutureLogBand",
    "FutureLogPage",
    "MonthlyCalendarList",
    "MonthlyTaskWell",
    "RapidLogPage",
    "EngineeringFace",
    "EngineeringPad",
    "FavoritesPage",
    "HabitGrid",
    "MeetingAgenda",
    "MeetingIndex",
    "MeetingSlot",
    "MonthCell",
    "MonthGrid",
    "MonthWeek",
    "My100Page",
    "Notes",
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
