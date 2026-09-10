"""Review index (month bands) and weekly dest — data only. Painters seat the well."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class ReviewWeek:
    """One linked week row on a month band — printed horizon, not a status mark."""

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
    """Minimal week-horizon index. Rows open weekly Review dests."""

    year: int
    dest: str
    quarter: int
    bands: tuple[ReviewMonthBand, ...]


@dataclass(frozen=True, slots=True)
class ReviewWeekPage:
    """Thesis B — three columns. Chip is Wnn → index. Chrome names the page."""

    year: int
    iso_year: int
    iso_week: int
    monday: date
    sunday: date
    index_dest: str
