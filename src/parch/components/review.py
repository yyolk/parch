"""Reviews index (month columns) and weekly dest — data only. Painters seat the well."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class ReviewWeek:
    """One linked week chip on a month column — printed horizon, not a status mark."""

    iso_year: int
    iso_week: int
    monday: date
    sunday: date
    dest: str


@dataclass(frozen=True, slots=True)
class ReviewsMonthColumn:
    """Calendar month header plus the unique touching weeks first seen in that month."""

    month: int
    name: str
    weeks: tuple[ReviewWeek, ...]


@dataclass(frozen=True, slots=True)
class ReviewsIndex:
    """Thesis A — month-column week-chip index. Chips open weekly Review dests."""

    year: int
    dest: str
    quarter: int
    columns: tuple[ReviewsMonthColumn, ...]


@dataclass(frozen=True, slots=True)
class ReviewWeekPage:
    """Weekly Review dest — thin lined notes stub. Chip is Wnn → index."""

    year: int
    iso_year: int
    iso_week: int
    monday: date
    sunday: date
    index_dest: str
