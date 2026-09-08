"""Monday-week calendar arithmetic for a single planner year."""

from __future__ import annotations

from calendar import Calendar
from datetime import date, timedelta

MONDAY = 0
_CAL = Calendar(firstweekday=MONDAY)

MONTHS = (
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
MONTHS_ABBR = (
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
DOW = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
DOW_LETTERS = ("M", "T", "W", "T", "F", "S", "S")


def quarter_of(month: int) -> int:
    return (month - 1) // 3 + 1


def quarter_months(quarter: int) -> tuple[int, int, int]:
    start = (quarter - 1) * 3 + 1
    return start, start + 1, start + 2


def days_in_year(year: int) -> list[date]:
    cur = date(year, 1, 1)
    end = date(year, 12, 31)
    out: list[date] = []
    while cur <= end:
        out.append(cur)
        cur += timedelta(days=1)
    return out


def weeks_spanning(year: int) -> list[date]:
    """Mondays of every week that touches `year`."""
    first = date(year, 1, 1)
    last = date(year, 12, 31)
    start = first - timedelta(days=first.weekday())
    end = last + timedelta(days=(6 - last.weekday()))
    mondays: list[date] = []
    cur = start
    while cur <= end:
        mondays.append(cur)
        cur += timedelta(days=7)
    return mondays


def month_weeks(year: int, month: int) -> list[list[date]]:
    return [list(week) for week in _CAL.monthdatescalendar(year, month)]


def mini_month_weeks(year: int, month: int) -> list[list[date]]:
    """Always six Monday-weeks so year/quarter grids share a rhythm."""
    weeks = month_weeks(year, month)
    while len(weeks) < 6:
        last = weeks[-1][-1]
        weeks.append([last + timedelta(days=i) for i in range(1, 8)])
    return weeks[:6]


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


def short_range(start: date, end: date) -> str:
    if start.month == end.month and start.year == end.year:
        return f"{start.day}-{end.day} {MONTHS_ABBR[start.month - 1]}"
    return (
        f"{start.day} {MONTHS_ABBR[start.month - 1]}"
        f" - {end.day} {MONTHS_ABBR[end.month - 1]}"
    )
