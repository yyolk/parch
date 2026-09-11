from parch.components.annual import AnnualGrid, AnnualMonth, AnnualMonthInk, AnnualMonthTypoNeeds
from parch.components.cover import CoverInk, CoverTitle, CoverTypoNeeds
from parch.components.habit import HabitGrid
from parch.components.header import HeaderChrome, HeaderInk, HeaderTypoNeeds
from parch.components.meeting import MeetingAgenda, MeetingIndex, MeetingSlot
from parch.components.month_grid import MonthCell, MonthGrid, MonthGridInk, MonthGridTypoNeeds, MonthWeek
from parch.components.notes import Notes, NotesInk, NotesTypoNeeds
from parch.components.priorities import Priorities, PrioritiesInk, PrioritiesTypoNeeds
from parch.components.projects import (
    ProjectTicket,
    ProjectTicketInk,
    ProjectTicketTypoNeeds,
    ProjectsBoard,
    ProjectsIndex,
)
from parch.components.quarter import QuarterGrid
from parch.components.review import (
    ReviewDay,
    ReviewIndex,
    ReviewMonthBand,
    ReviewWeek,
    ReviewWeekPage,
)
from parch.components.schedule import Schedule, ScheduleInk, ScheduleTypoNeeds
from parch.components.tasks import TaskWeek, TasksIndex, TasksMonthBand, TasksWeekPage
from parch.components.week import WeekDay, WeekDayInk, WeekDayTypoNeeds, WeekStrip

type Component = (
    AnnualGrid
    | AnnualMonth
    | CoverTitle
    | HabitGrid
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
    | TaskWeek
    | TasksIndex
    | TasksMonthBand
    | TasksWeekPage
    | WeekStrip
)

__all__ = [
    "AnnualGrid",
    "AnnualMonth",
    "AnnualMonthInk",
    "AnnualMonthTypoNeeds",
    "Component",
    "CoverInk",
    "CoverTitle",
    "CoverTypoNeeds",
    "HabitGrid",
    "HeaderChrome",
    "HeaderInk",
    "HeaderTypoNeeds",
    "MeetingAgenda",
    "MeetingIndex",
    "MeetingSlot",
    "MonthCell",
    "MonthGrid",
    "MonthGridInk",
    "MonthGridTypoNeeds",
    "MonthWeek",
    "Notes",
    "NotesInk",
    "NotesTypoNeeds",
    "Priorities",
    "PrioritiesInk",
    "PrioritiesTypoNeeds",
    "ProjectTicket",
    "ProjectTicketInk",
    "ProjectTicketTypoNeeds",
    "ProjectsBoard",
    "ProjectsIndex",
    "QuarterGrid",
    "ReviewDay",
    "ReviewIndex",
    "ReviewMonthBand",
    "ReviewWeek",
    "ReviewWeekPage",
    "Schedule",
    "ScheduleInk",
    "ScheduleTypoNeeds",
    "TaskWeek",
    "TasksIndex",
    "TasksMonthBand",
    "TasksWeekPage",
    "WeekDay",
    "WeekDayInk",
    "WeekDayTypoNeeds",
    "WeekStrip",
]
