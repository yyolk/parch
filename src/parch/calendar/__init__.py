"""Slim calendar: one month, Monday-first weeks."""

import calendar as pycal
from datetime import date, timedelta

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

WEEKDAY_LABELS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
WEEKDAY_FULL = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)


def month_name(month: int) -> str:
    return MONTH_NAMES[month - 1]


def weekday_labels(weekday_start: int) -> tuple[str, ...]:
    return tuple(WEEKDAY_LABELS[(weekday_start + i) % 7] for i in range(7))


def month_weeks(year: int, month: int, weekday_start: int = 0) -> list[list[date | None]]:
    cal = pycal.Calendar(firstweekday=weekday_start)
    weeks: list[list[date | None]] = []
    for week in cal.monthdatescalendar(year, month):
        weeks.append([d if d.month == month else None for d in week])
    return weeks


def month_touching_weeks(year: int, month: int, weekday_start: int = 0) -> list[list[date]]:
    """Full 7-day weeks that contain at least one day of the month (adjacent days kept)."""
    cal = pycal.Calendar(firstweekday=weekday_start)
    return [list(week) for week in cal.monthdatescalendar(year, month)]


def iso_monday(day: date) -> date:
    """Monday of the ISO week that contains ``day`` (weekday_start=monday books)."""
    return day - timedelta(days=day.weekday())


def short_date_range(start: date, end: date) -> str:
    if start.month == end.month:
        return f"{start.day}–{end.day} {MONTH_NAMES[start.month - 1][:3]}"
    left = f"{start.day} {MONTH_NAMES[start.month - 1][:3]}"
    right = f"{end.day} {MONTH_NAMES[end.month - 1][:3]}"
    return f"{left}–{right}"


def month_days(year: int, month: int) -> list[date]:
    last = pycal.monthrange(year, month)[1]
    return [date(year, month, day) for day in range(1, last + 1)]
