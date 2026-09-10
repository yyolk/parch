"""Tasks index and weekly dest — data only. Painters seat the week chips and two-column well."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class TaskWeek:
    """One numbered week chip — the dest hit. Printed range stays unlinkable."""

    iso_year: int
    iso_week: int
    monday: date
    sunday: date
    dest: str


@dataclass(frozen=True, slots=True)
class TasksIndex:
    """Thesis F — two-column numbered week chip list. Chip per week is the dest hit."""

    year: int
    dest: str
    weeks: tuple[TaskWeek, ...]


@dataclass(frozen=True, slots=True)
class WeeklyTasks:
    """Thesis F dest — Morning | Later checklists, leftover notes full width."""

    year: int
    iso_week: int
    monday: date
    sunday: date
    morning: int
    later: int
    index_dest: str = ""
    number: int = 0
