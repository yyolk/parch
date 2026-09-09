"""Annual year grid — data only. Only pressed-month dests are set."""

from dataclasses import dataclass

from parch.components.month_grid import MonthWeek


@dataclass(frozen=True, slots=True)
class AnnualMonth:
    month: int
    name: str
    dest: str | None
    weekday_labels: tuple[str, ...]
    weeks: tuple[MonthWeek, ...]


@dataclass(frozen=True, slots=True)
class AnnualGrid:
    year: int
    months: tuple[AnnualMonth, ...]
