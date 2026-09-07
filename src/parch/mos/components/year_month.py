"""Compact Nomad year-month cell (not LittleCalendar / month_grid)."""

from parch.calendar.day import Day
from parch.calendar.month import Month
from parch.i18n import I18n
from parch.mos.manifest import Manifest

WEEK_ROWS = 6


def year_month_cell(i18n: I18n, manifest: Manifest, month: Month) -> str:
    header = manifest.link_or_content(month.id, i18n.t(f"months.short.{month.name}"))
    sample = _expand_weeks(month)[0]
    letters = ", ".join(
        f'[{i18n.t(f"weekday.letter.{day.weekday_name}")}]' for day in sample
    )
    rows = []
    for week in _padded_weeks(month):
        rows.append(", ".join(_day_cell(manifest, month, day) for day in week))
    body = f"""grid(
  columns: (1fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr),
  rows: (auto,) + (1fr,) * {WEEK_ROWS},
  align: center + horizon,
  {letters},
  {", ".join(rows)}
)"""
    return f"year-month({header}, {body})"


def _day_cell(manifest: Manifest, month: Month, day: Day | None) -> str:
    if day is None:
        return "[]"
    return manifest.link_or_content(day.id, str(day.month_day))


def _padded_weeks(month: Month) -> list[list[Day | None]]:
    weeks = []
    for week in _expand_weeks(month):
        weeks.append([day if day.month() == month else None for day in week])
    empty = [None] * 7
    while len(weeks) < WEEK_ROWS:
        weeks.append(list(empty))
    return weeks[:WEEK_ROWS]


def _expand_weeks(month: Month) -> list[list[Day]]:
    first = month.day.beginning_of_week()
    last = month.day.end_of_week()
    ranges = [_days_inclusive(first, last)]
    while ranges[-1][-1].month() == month:
        prev_end = ranges[-1][-1]
        ranges.append(_days_inclusive(prev_end + 1, prev_end + 7))
    return ranges


def _days_inclusive(start: Day, end: Day) -> list[Day]:
    out = []
    current = start
    while current <= end:
        out.append(current)
        current = current.succ()
    return out
