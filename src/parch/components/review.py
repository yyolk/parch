"""Review index (flat week list) and weekly dest — data only. Painters seat the well."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class ReviewWeek:
    """One linked week row on the minimal index — printed horizon, not a score."""

    iso_year: int
    iso_week: int
    monday: date
    sunday: date
    dest: str


@dataclass(frozen=True, slots=True)
class ReviewIndex:
    """Minimal quarter index. Rows open weekly Review dests. No month bands."""

    year: int
    dest: str
    quarter: int
    weeks: tuple[ReviewWeek, ...]


@dataclass(frozen=True, slots=True)
class ReviewWeekPage:
    """Thesis D — Accomplishments (~½) over Carry forward + Grateful for. Chip is Wnn → index."""

    year: int
    iso_year: int
    iso_week: int
    monday: date
    sunday: date
    carry_rows: int
    index_dest: str
