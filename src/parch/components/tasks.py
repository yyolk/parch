"""Tasks index (month bands) and weekly dest — data only. Painters seat the well."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class TaskWeek:
    """One linked week row on a month band — printed horizon, not a status mark."""

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
    """Thesis C — month-banded week-horizon index. Rows open weekly Tasks dests."""

    year: int
    dest: str
    quarter: int
    bands: tuple[TasksMonthBand, ...]


@dataclass(frozen=True, slots=True)
class TasksWeekPage:
    """Weekly Tasks dest — unlabeled ⅔ checklist over leftover notes. Chip is Wnn → index."""

    year: int
    iso_year: int
    iso_week: int
    monday: date
    sunday: date
    rows: int
    index_dest: str
