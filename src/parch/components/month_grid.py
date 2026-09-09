"""Month grid — data only. Linked days carry a dest; others do not."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MonthCell:
    day: int | None
    dest: str | None = None


@dataclass(frozen=True)
class MonthGrid:
    year: int
    month: int
    month_name: str
    weekday_labels: tuple[str, ...]
    weeks: tuple[tuple[MonthCell, ...], ...]
