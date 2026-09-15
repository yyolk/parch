"""Bullet journal components — data only. Painters seat the wells."""

from dataclasses import dataclass
from datetime import date

# Sealed grouping — not a Spec/TOML knob until a second future-log path exists.
FUTURE_LOG_MONTHS_PER_PAGE = 3


@dataclass(frozen=True, slots=True)
class BujoKey:
    """Printed legend plus blank custom-signifier rows."""

    symbols: tuple[tuple[str, str], ...]
    custom_rows: int = 4


@dataclass(frozen=True, slots=True)
class BujoIndexRow:
    label: str
    dest: str | None = None


@dataclass(frozen=True, slots=True)
class BujoIndex:
    year: int
    page: int
    pages: int
    rows: tuple[BujoIndexRow, ...]


@dataclass(frozen=True, slots=True)
class FutureLogBand:
    month: int
    name: str
    dest: str


@dataclass(frozen=True, slots=True)
class FutureLogPage:
    year: int
    page: int
    pages: int
    months: tuple[FutureLogBand, ...]


@dataclass(frozen=True, slots=True)
class CalendarDayRow:
    day: int
    weekday: str
    dest: str


@dataclass(frozen=True, slots=True)
class MonthlyCalendarList:
    year: int
    month: int
    month_name: str
    days: tuple[CalendarDayRow, ...]
    tasks_dest: str


@dataclass(frozen=True, slots=True)
class MonthlyTaskWell:
    year: int
    month: int
    month_name: str
    calendar_dest: str
    migrate_lines: int = 3


@dataclass(frozen=True, slots=True)
class RapidLogDay:
    moment: date
    title: str
    dest: str


@dataclass(frozen=True, slots=True)
class RapidLogPage:
    year: int
    days: tuple[RapidLogDay, ...]


@dataclass(frozen=True, slots=True)
class CollectionLeaf:
    year: int
    number: int
    index_dest: str
