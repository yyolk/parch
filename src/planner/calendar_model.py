"""Monday-start calendar model for a single year. No Typst/parch types."""

from __future__ import annotations

from calendar import Calendar
from dataclasses import dataclass
from datetime import date, timedelta


WEEKDAY_LETTERS = ("M", "T", "W", "T", "F", "S", "S")
MONTH_NAMES = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)
MONTH_ABBR = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)


def monday_on_or_before(day: date) -> date:
    return day - timedelta(days=day.weekday())


def sunday_on_or_after(day: date) -> date:
    return day + timedelta(days=(6 - day.weekday()))


@dataclass(frozen=True)
class Week:
    monday: date

    @property
    def days(self) -> tuple[date, ...]:
        return tuple(self.monday + timedelta(days=i) for i in range(7))

    @property
    def sunday(self) -> date:
        return self.monday + timedelta(days=6)

    def overlaps_year(self, year: int) -> bool:
        return any(d.year == year for d in self.days)

    def dest(self) -> str:
        return f"week-{self.monday.isoformat()}"


@dataclass(frozen=True)
class YearPlan:
    """All dates and Monday-start weeks that touch ``year``."""

    year: int

    @property
    def jan1(self) -> date:
        return date(self.year, 1, 1)

    @property
    def dec31(self) -> date:
        return date(self.year, 12, 31)

    @property
    def days(self) -> tuple[date, ...]:
        n = (self.dec31 - self.jan1).days + 1
        return tuple(self.jan1 + timedelta(days=i) for i in range(n))

    @property
    def weeks(self) -> tuple[Week, ...]:
        start = monday_on_or_before(self.jan1)
        end = sunday_on_or_after(self.dec31)
        weeks: list[Week] = []
        cursor = start
        while cursor <= end:
            weeks.append(Week(monday=cursor))
            cursor += timedelta(days=7)
        return tuple(weeks)

    def month_grid(self, month: int) -> list[list[date]]:
        return Calendar(firstweekday=0).monthdatescalendar(self.year, month)

    def week_containing(self, day: date) -> Week:
        return Week(monday=monday_on_or_before(day))

    def quarter_months(self, quarter: int) -> tuple[int, int, int]:
        first = (quarter - 1) * 3 + 1
        return (first, first + 1, first + 2)


def dest_year() -> str:
    return "year"


def dest_quarters() -> str:
    return "quarters"


def dest_quarter(n: int) -> str:
    return f"q{n}"


def dest_months() -> str:
    return "months"


def dest_month(month: int) -> str:
    return f"month-{month:02d}"


def dest_weeks() -> str:
    return "weeks"


def dest_days() -> str:
    return "days"


def dest_day(day: date) -> str:
    return f"day-{day.isoformat()}"


def dest_cover() -> str:
    return "cover"
