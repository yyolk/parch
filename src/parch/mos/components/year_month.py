"""Compact Nomad year-month / mini-month cells (locked densify, not LittleCalendar)."""

from parch.calendar import walk
from parch.calendar.month import Month
from parch.i18n import I18n
from parch.mos.manifest import Manifest


def month_start_wd(month: Month) -> int:
    first = month.day
    start_wd = 0
    cursor = first.beginning_of_week()
    while cursor < first:
        start_wd += 1
        cursor = cursor + 1
    return start_wd


def month_day_dests(manifest: Manifest, month: Month) -> str:
    """Typst array of dests, index 0 = day 1. ``none`` when that daily page is off."""
    dests = [manifest.dest(day.id) for day in walk(month.day, month.day.end_of_month())]
    return f"({', '.join(dests)},)"


def year_month_cell(i18n: I18n, manifest: Manifest, month: Month) -> str:
    name = i18n.t(f"months.full.{month.name}")
    header = manifest.link_or_content(month.id, name)
    days = month.day.end_of_month().month_day
    return (
        f"year-month({header}, start-wd: {month_start_wd(month)}, days: {days}, "
        f"dests: {month_day_dests(manifest, month)})"
    )


def mini_month_cell(
    i18n: I18n,
    manifest: Manifest,
    month: Month,
    highlight: int | None = None,
    day_h: str = "2.2mm",
    weeks: int = 6,
    compact: bool = True,
) -> str:
    name = i18n.t(f"months.full.{month.name}")
    header = manifest.link_or_content(month.id, name)
    days = month.day.end_of_month().month_day
    hl = "none" if highlight is None else str(highlight)
    compact_s = "true" if compact else "false"
    return (
        f"mini-month({header}, start-wd: {month_start_wd(month)}, days: {days}, "
        f"highlight: {hl}, day-h: {day_h}, weeks: {weeks}, compact: {compact_s})"
    )
