from parch.components.cover import CoverTitle
from parch.components.month_grid import MonthCell, MonthGrid, MonthWeek
from parch.components.notes import Notes
from parch.components.schedule import Schedule

type Component = CoverTitle | MonthGrid | Notes | Schedule

__all__ = [
    "Component",
    "CoverTitle",
    "MonthCell",
    "MonthGrid",
    "MonthWeek",
    "Notes",
    "Schedule",
]
