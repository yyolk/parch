from parch.components.annual import AnnualGrid, AnnualMonth
from parch.components.cover import CoverTitle
from parch.components.habit import HabitGrid
from parch.components.meeting import MeetingAgenda, MeetingIndex, MeetingSlot
from parch.components.month_grid import MonthCell, MonthGrid, MonthWeek
from parch.components.notes import Notes
from parch.components.priorities import Priorities
from parch.components.projects import ProjectTicket, ProjectsBoard, ProjectsIndex
from parch.components.quarter import QuarterGrid
from parch.components.schedule import Schedule
from parch.components.week import WeekDay, WeekStrip

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
    | Schedule
    | WeekStrip
)

__all__ = [
    "AnnualGrid",
    "AnnualMonth",
    "Component",
    "CoverTitle",
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
    "Schedule",
    "WeekDay",
    "WeekStrip",
]
