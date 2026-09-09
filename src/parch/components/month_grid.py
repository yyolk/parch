"""Month grid — data only. Linked days carry a dest; others do not."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MonthCell:
    day: int | None
    dest: str | None = None


type MonthWeek = tuple[MonthCell, ...]


@dataclass(frozen=True, slots=True)
class MonthGrid:
    year: int
    month: int
    month_name: str
    weekday_labels: tuple[str, ...]
    weeks: tuple[MonthWeek, ...]
    week_dests: tuple[str, ...]
