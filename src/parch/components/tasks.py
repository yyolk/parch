"""Tasks C×F hybrid — month bands + packed week chips, Morning|Later dest. Data only."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class TaskWeek:
    """One packed ISO week chip — the dest hit. Printed range stays unlinkable."""

    iso_year: int
    iso_week: int
    monday: date
    sunday: date
    dest: str


@dataclass(frozen=True, slots=True)
class TasksMonthBand:
    """Calendar month header plus the unique touching weeks first seen in that month."""

    month: int
    name: str
    weeks: tuple[TaskWeek, ...]


@dataclass(frozen=True, slots=True)
class TasksIndex:
    """C×F — month-banded index; each band packs two-column week chips."""

    year: int
    dest: str
    quarter: int
    bands: tuple[TasksMonthBand, ...]


@dataclass(frozen=True, slots=True)
class WeeklyTasks:
    """F dest — Morning | Later checklists, leftover notes full width."""

    year: int
    iso_year: int
    iso_week: int
    monday: date
    sunday: date
    morning: int
    later: int
    index_dest: str
