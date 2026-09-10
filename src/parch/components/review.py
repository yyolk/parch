"""Review index (month bands × week chips) and weekly dest — data only."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class ReviewWeek:
    """One linked week chip on a month band — first-class week, not a status mark."""

    iso_year: int
    iso_week: int
    monday: date
    sunday: date
    dest: str


@dataclass(frozen=True, slots=True)
class ReviewMonthBand:
    """Calendar month header plus the unique touching weeks first seen in that month."""

    month: int
    name: str
    weeks: tuple[ReviewWeek, ...]


@dataclass(frozen=True, slots=True)
class ReviewIndex:
    """Thesis C — month-banded week-chip index. Chips open weekly Review dests."""

    year: int
    dest: str
    quarter: int
    bands: tuple[ReviewMonthBand, ...]


@dataclass(frozen=True, slots=True)
class ReviewWeekPage:
    """Thin weekly Review dest stub. Chip is Wnn → owning quarter index."""

    year: int
    iso_year: int
    iso_week: int
    monday: date
    sunday: date
    index_dest: str
