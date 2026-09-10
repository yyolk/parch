from parch.components.annual import AnnualGrid, AnnualMonth
from parch.components.cover import CoverTitle
from parch.components.habit import HabitGrid
from parch.components.month_grid import MonthCell, MonthGrid, MonthWeek
from parch.components.notes import Notes
from parch.components.priorities import Priorities
from parch.components.projects import ProjectsBoard
from parch.components.projects_index_alpha import (
    ProjectIndexEntry,
    ProjectLeaf,
    ProjectsIndexAlpha,
)
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
    | ProjectLeaf
    | ProjectsBoard
    | ProjectsIndexAlpha
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
    "ProjectIndexEntry",
    "ProjectLeaf",
    "ProjectsBoard",
    "ProjectsIndexAlpha",
    "QuarterGrid",
    "Schedule",
    "WeekDay",
    "WeekStrip",
]
