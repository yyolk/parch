"""Review index (week stub) and weekly dest — data only. Painters seat the well."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class ReviewWeek:
    """One linked week row on a quarter index — printed horizon, not a status mark."""

    iso_year: int
    iso_week: int
    monday: date
    sunday: date
    dest: str


@dataclass(frozen=True, slots=True)
class ReviewsIndex:
    """Minimal quarter landing. Rows open weekly Review dests so Rev / Wnn have a home."""

    year: int
    dest: str
    quarter: int
    weeks: tuple[ReviewWeek, ...]


@dataclass(frozen=True, slots=True)
class ReviewWeekPage:
    """Thesis A — stacked Wins → Lessons → Next week → leftover Notes. Chip is Wnn → index."""

    year: int
    iso_year: int
    iso_week: int
    monday: date
    sunday: date
    index_dest: str
