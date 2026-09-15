from parch.components.annual import AnnualGrid, AnnualMonth
from parch.components.bujo import (
    BujoIndex,
    BujoIndexRow,
    BujoKey,
    CalendarDayRow,
    CollectionLeaf,
    FutureLogBand,
    FutureLogPage,
    MonthlyCalendarList,
    MonthlyTaskWell,
    RapidLogPage,
)
from parch.components.cover import CoverTitle
from parch.components.engineering import EngineeringFace, EngineeringPad
from parch.components.habit import HabitGrid
from parch.components.meeting import MeetingAgenda, MeetingIndex, MeetingSlot
from parch.components.month_grid import MonthCell, MonthGrid, MonthWeek
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
    | BujoKey
    | CollectionLeaf
    | CoverTitle
    | EngineeringPad
    | FutureLogPage
    | HabitGrid
    | MonthlyCalendarList
    | MonthlyTaskWell
    | RapidLogPage
    | MeetingAgenda
    | MeetingIndex
    | MeetingSlot
    | MonthGrid
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
    "BujoIndexRow",
    "BujoKey",
    "CalendarDayRow",
    "CollectionLeaf",
    "Component",
    "CoverTitle",
    "FutureLogBand",
    "FutureLogPage",
    "MonthlyCalendarList",
    "MonthlyTaskWell",
    "RapidLogPage",
    "EngineeringFace",
    "EngineeringPad",
    "HabitGrid",
    "MeetingAgenda",
    "MeetingIndex",
    "MeetingSlot",
    "MonthCell",
    "MonthGrid",
    "MonthWeek",
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
