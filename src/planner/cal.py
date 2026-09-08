"""Monday-week calendar helpers for a single planner year."""

from __future__ import annotations

from calendar import Calendar
from datetime import date, timedelta
from typing import Iterator

_MONDAY_CAL = Calendar(firstweekday=0)

WEEKDAY_SHORT = ("M", "T", "W", "T", "F", "S", "S")
WEEKDAY_MED = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
MONTH_NAMES = (
    "",
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
MONTH_SHORT = (
    "",
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


def days_in_year(year: int) -> list[date]:
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    out: list[date] = []
    cur = start
    while cur <= end:
        out.append(cur)
        cur += timedelta(days=1)
    return out


def weeks_spanning(year: int) -> list[list[date]]:
    cur = monday_on_or_before(date(year, 1, 1))
    last = sunday_on_or_after(date(year, 12, 31))
    weeks: list[list[date]] = []
    while cur <= last:
        weeks.append([cur + timedelta(days=i) for i in range(7)])
        cur += timedelta(days=7)
    return weeks


def month_grid(year: int, month: int) -> list[list[date]]:
    return _MONDAY_CAL.monthdatescalendar(year, month)


def dest_cover() -> str:
    return "cover"


def dest_year() -> str:
    return "year"


def dest_quarter(q: int) -> str:
    return f"q{q}"


def dest_month(month: int) -> str:
    return f"month-{month:02d}"


def dest_week(monday: date) -> str:
    return f"week-{monday.isoformat()}"


def dest_day(day: date) -> str:
    return f"day-{day.isoformat()}"


def dest_notes(day: date, n: int) -> str:
    return f"day-{day.isoformat()}-notes-{n}"


def iter_year_days(year: int) -> Iterator[date]:
    yield from days_in_year(year)
