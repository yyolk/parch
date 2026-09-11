"""Habit tracker grid — data only. Blank name slots × day check cells."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HabitGrid:
    year: int
    month: int
    month_name: str
    days: int
    rows: int
    month_dest: str
    day_dests: tuple[str, ...]
    quarter_dest: str | None = None
