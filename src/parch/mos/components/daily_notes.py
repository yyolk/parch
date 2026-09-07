"""Daily notes block on the day page."""

from typing import Any

from parch.calendar.dated_note import DatedNote
from parch.calendar.day import Day
from parch.i18n import I18n
from parch.mos.manifest import Manifest
from parch.mos.preamble import _WELL_PATTERN


class DailyNotes:
    def __init__(
        self,
        i18n: I18n,
        manifest: Manifest,
        day: Day,
        title_height: str,
        notes_height: str,
        pattern: str = "dotted",
        more_chip: bool = False,
        chip_font: str | None = None,
        **_rest: Any,
    ) -> None:
        self.i18n = i18n
        self.manifest = manifest
        self.day = day
        self.title_height = title_height
        self.notes_height = notes_height
        self.pattern = pattern
        self.more_chip = more_chip
        self.chip_font = chip_font

    def generate(self) -> str:
        daily_note_id = DatedNote(weekday_start=self.day.weekday_start, day=self.day).id
        notes = self.i18n.t("daily_notes")
        rule = "stroke: (bottom: regular_stroke + black)"
        if self.manifest.source(daily_note_id):
            more = self.manifest.link_or_content(daily_note_id, self.i18n.t("more_daily_notes"))
            if self.chip_font:
                more = f'text(size: 7pt, font: "{self.chip_font}", {more})'
            if self.more_chip:
                more = (
                    "box(inset: (x: 1.4mm, y: 0.35mm), "
                    f"stroke: regular_stroke + black, {more})"
                )
            return f"""grid(
  columns: (1fr, auto),
  rows: ({self.title_height}, {self.notes_height}),
  grid.cell(align: horizon, {rule}, [{notes}]),
  grid.cell(align: horizon + right, {rule}, {more}),
  grid.cell(colspan: 2, lined_well({_WELL_PATTERN.get(self.pattern, self.pattern)}))
)"""
        return f"""grid(
  columns: 1fr,
  rows: ({self.title_height}, {self.notes_height}),
  grid.cell(align: horizon, {rule}, [{notes}]),
  lined_well({_WELL_PATTERN.get(self.pattern, self.pattern)})
)"""
