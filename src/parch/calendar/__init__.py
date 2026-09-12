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


def quarter_of(month: int) -> int:
    return (month - 1) // 3 + 1


def months_in_quarter(quarter: int) -> tuple[int, int, int]:
    start = (quarter - 1) * 3 + 1
    return (start, start + 1, start + 2)


def weekday_labels(weekday_start: int) -> tuple[str, ...]:
    return tuple(WEEKDAY_LABELS[(weekday_start + i) % 7] for i in range(7))


def month_weeks(
    year: int, month: int, weekday_start: int = 0
) -> list[list[date | None]]:
    cal = pycal.Calendar(firstweekday=weekday_start)
    weeks: list[list[date | None]] = []
    for week in cal.monthdatescalendar(year, month):
        weeks.append([d if d.month == month else None for d in week])
    return weeks


def month_touching_weeks(
    year: int, month: int, weekday_start: int = 0
) -> list[list[date]]:
    """Full 7-day weeks that contain at least one day of the month (adjacent days kept)."""
    cal = pycal.Calendar(firstweekday=weekday_start)
    return [list(week) for week in cal.monthdatescalendar(year, month)]


def months_touching_weeks(
    year: int, months: tuple[int, ...], weekday_start: int = 0
) -> list[list[date]]:
    """ISO/Monday weeks that touch any of ``months``, each week once (first seen)."""
    return [
        week
        for _month, weeks in month_week_bands(year, months, weekday_start)
        for week in weeks
    ]


def month_week_bands(
    year: int, months: tuple[int, ...], weekday_start: int = 0
) -> list[tuple[int, list[list[date]]]]:
    """Month → unique touching weeks (first seen). Horizon bands, not status partitions."""
    seen: set[tuple[int, int]] = set()
    out: list[tuple[int, list[list[date]]]] = []
    for month in months:
        weeks: list[list[date]] = []
        for week in month_touching_weeks(year, month, weekday_start):
            monday = next((d for d in week if d.weekday() == 0), iso_monday(week[0]))
            key = (monday.isocalendar().year, monday.isocalendar().week)
            if key in seen:
                continue
            seen.add(key)
            weeks.append(week)
        if weeks:
            out.append((month, weeks))
    return out


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
