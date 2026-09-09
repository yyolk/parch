"""Weekly strip — data only. Linked in-month days carry a dest."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class WeekDay:
    day: date
    weekday_label: str
    dest: str | None
    in_month: bool


@dataclass(frozen=True, slots=True)
class WeekStrip:
    iso_year: int
    iso_week: int
    monday: date
    sunday: date
    days: tuple[WeekDay, ...]
