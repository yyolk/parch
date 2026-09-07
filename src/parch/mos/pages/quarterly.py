"""Quarter page: three little calendars + scratch pad."""

from typing import Any

from parch.calendar.quarter import Quarter
from parch.i18n import I18n
from parch.mos.components.little_calendar import LittleCalendar
from parch.mos.manifest import Manifest
from parch.mos.components.year_month import year_month_cell
from parch.mos.preamble import _WELL_PATTERN


class Quarterly:
    def __init__(
        self,
        i18n: I18n,
        manifest: Manifest,
        quarter: Quarter,
        little_calendar: dict[str, Any],
        pattern: str = "dotted",
        side: str = "left",
    ) -> None:
        self.i18n = i18n
        self.manifest = manifest
        self.quarter = quarter
        self.little_calendar = little_calendar
        self.pattern = pattern
        self.side = side

    def title(self) -> str:
        return f'text(size: h1)[{self.i18n.t("quarter.long")} {self.quarter.number} <{self.quarter.id}>]'

    def content(self) -> str:
        months = self._months_grid()
        pad = f"lined_well({_WELL_PATTERN.get(self.pattern, self.pattern)})"
        return f"quarter_well({self.side}, {months}, {pad})"

    def nomad_content(self) -> str:
        """Locked Nomad quarterly: 26mm month strip + Focus / Notes wells."""
        months = ", ".join(
            year_month_cell(self.i18n, self.manifest, month)
            for month in self.quarter.months()
        )
        strip = f"""grid(
  columns: (1fr, 1fr, 1fr),
  rows: 1fr,
  column-gutter: 1.2mm,
  {months}
)"""
        ticks = ",\n    ".join(
            ["box(height: regular_height, align(horizon + start, task_tick()))"] * 6
        )
        focus = f"""grid(
  columns: 1fr,
  rows: (auto, auto),
  block(inset: (top: 0.4mm, bottom: 0.3mm), text(weight: "bold")[{self.i18n.t("focus")}]),
  grid(
    columns: 1fr,
    rows: ({", ".join(["regular_height"] * 6)}),
    stroke: (_, _) => (bottom: regular_stroke + black),
    inset: 0pt,
    {ticks}
  )
)"""
        notes = f"""grid(
  columns: 1fr,
  rows: (auto, 1fr),
  block(inset: (top: 0.4mm, bottom: 0.3mm), text(weight: "bold")[{self.i18n.t("notes")}]),
  lined_well(lined_fill)
)"""
        return f"nomad_quarter_well({strip}, {focus}, {notes})"

    def _months_grid(self) -> str:
        months = self._months()
        # Bound each month to an equal 1fr row. A stack + LittleCalendar
        # rows: 1fr lets the first month consume the whole column.
        rows = ", ".join(["1fr"] * len(months))
        return f"""grid(
  columns: 1fr,
  rows: ({rows}),
  row-gutter: regular_column_gutter,

  {", ".join(months)}
)"""

    def _months(self) -> list[str]:
        params = {**self.little_calendar, "show_week_letter": False}
        return [
            LittleCalendar(
                i18n=self.i18n,
                manifest=self.manifest,
                month=month,
                **params,
                side=self.side,
            ).generate()
            for month in self.quarter.months()
        ]
