"""Compact Nomad year-month cell (locked densify, not LittleCalendar)."""

from parch.calendar.month import Month
from parch.i18n import I18n
from parch.mos.manifest import Manifest


def year_month_cell(i18n: I18n, manifest: Manifest, month: Month) -> str:
    name = i18n.t(f"months.full.{month.name}")
    header = manifest.link_or_content(month.id, name)
    first = month.day
    start_wd = 0
    cursor = first.beginning_of_week()
    while cursor < first:
        start_wd += 1
        cursor = cursor + 1
    days = first.end_of_month().month_day
    return f"year-month({header}, start-wd: {start_wd}, days: {days})"
