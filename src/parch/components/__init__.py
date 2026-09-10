from parch.components.annual import AnnualGrid, AnnualMonth
from parch.components.cover import CoverTitle
from parch.components.habit import HabitGrid
from parch.components.month_grid import MonthCell, MonthGrid, MonthWeek
from parch.components.notes import Notes
from parch.components.priorities import Priorities
from parch.components.projects import (
    ProjectEntry,
    ProjectLeaf,
    ProjectsBoard,
    ProjectsIndex,
    SAMPLE_PROJECTS,
    sample_projects,
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
    | ProjectEntry
    | ProjectLeaf
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
    "ProjectEntry",
    "ProjectLeaf",
    "ProjectsBoard",
    "ProjectsIndex",
    "SAMPLE_PROJECTS",
    "QuarterGrid",
    "sample_projects",
    "Schedule",
    "WeekDay",
    "WeekStrip",
]
