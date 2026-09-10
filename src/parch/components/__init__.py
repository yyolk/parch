from parch.components.annual import AnnualGrid, AnnualMonth
from parch.components.cover import CoverTitle
from parch.components.habit import HabitGrid
from parch.components.month_grid import MonthCell, MonthGrid, MonthWeek
from parch.components.notes import Notes
from parch.components.priorities import Priorities
from parch.components.project_sheet import ProjectSheet
from parch.components.projects import ProjectsBoard
from parch.components.projects_index import ProjectsIndex
from parch.components.quarter import QuarterGrid
from parch.components.schedule import Schedule
from parch.components.week import WeekDay, WeekStrip

type Component = (
    AnnualGrid
    | AnnualMonth
    | CoverTitle
    | HabitGrid
    | MonthGrid
    | Notes
    | Priorities
    | ProjectSheet
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
    "MonthCell",
    "MonthGrid",
    "MonthWeek",
    "Notes",
    "Priorities",
    "ProjectSheet",
    "ProjectsBoard",
    "ProjectsIndex",
    "QuarterGrid",
    "Schedule",
    "WeekDay",
    "WeekStrip",
]
