"""Review index (week grid) and weekly dest — data only. Painters seat the well."""

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
    """One linked week chip on the year grid — printed horizon, not a status mark."""

    iso_year: int
    iso_week: int
    monday: date
    sunday: date
    dest: str


@dataclass(frozen=True, slots=True)
class ReviewMonthBand:
    """Calendar month plus the unique touching weeks first seen in that month."""

    month: int
    name: str
    weeks: tuple[ReviewWeek, ...]


@dataclass(frozen=True, slots=True)
class ReviewIndex:
    """Multi-column week-chip grid for ``paint_review_index``. Month headers + hairlines read across."""

    year: int
    dest: str
    bands: tuple[ReviewMonthBand, ...]


@dataclass(frozen=True, slots=True)
class ReviewWeekPage:
    """Weekly dest for ``paint_review`` — seven day cues over a week narrative well. Chip is Wnn → index."""

    year: int
    iso_year: int
    iso_week: int
    monday: date
    sunday: date
    days: tuple[ReviewDay, ...]
    index_dest: str
