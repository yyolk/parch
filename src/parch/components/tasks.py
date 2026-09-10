"""Tasks index and weekly dest — data only. Painters seat the roster and well."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class TaskWeek:
    """One dense roster row — week-label stub hits the weekly Tasks dest; title stays unlinkable."""

    iso_year: int
    iso_week: int
    monday: date
    sunday: date
    dest: str


@dataclass(frozen=True, slots=True)
class TasksIndex:
    """Thesis A — dense week roster. Stub per row is the dest hit; title write-in stays unlinkable."""

    year: int
    dest: str
    weeks: tuple[TaskWeek, ...]


@dataclass(frozen=True, slots=True)
class WeekTasks:
    """Weekly Tasks dest. Ticket dests set ``index_dest`` (header chip + lit Task)."""

    year: int
    iso_week: int
    monday: date
    sunday: date
    tasks: int
    index_dest: str = ""
