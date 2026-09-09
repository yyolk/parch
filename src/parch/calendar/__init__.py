"""Slim calendar: one month, Monday-first weeks."""

import calendar as pycal
from datetime import date

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
