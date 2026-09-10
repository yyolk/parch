"""Review index (week roster) and weekly dest — data only. Painters seat the well."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class ReviewDay:
    """One Mon–Sun cue on the dest strip — label may link; write-in stays unlinkable."""

    day: date
    weekday_label: str
    dest: str | None


@dataclass(frozen=True, slots=True)
class ReviewWeek:
    """One linked week row on the thin index — printed horizon, not a status mark."""

    iso_year: int
    iso_week: int
    monday: date
    sunday: date
    dest: str


@dataclass(frozen=True, slots=True)
class ReviewIndex:
    """Minimal Review index — week rows open weekly Review dests. Nav/links only."""

    year: int
    dest: str
    quarter: int
    weeks: tuple[ReviewWeek, ...]


@dataclass(frozen=True, slots=True)
class ReviewWeekPage:
    """Thesis E — seven day cues over a week narrative well. Chip is Wnn → index."""

    year: int
    iso_year: int
    iso_week: int
    monday: date
    sunday: date
    days: tuple[ReviewDay, ...]
    index_dest: str
