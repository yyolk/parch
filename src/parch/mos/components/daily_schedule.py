"""Hourly schedule block on the day page."""

from datetime import datetime
from typing import Any

from parch.i18n import I18n


class DailySchedule:
    def __init__(
        self,
        i18n: I18n,
        from_: int | None = None,
        to: int | None = None,
        trailing_30_minutes: bool = True,
        time_format: str = "%k",
        stretch: bool = False,
        **rest: Any,
    ) -> None:
        self.i18n = i18n
        # YAML key is `from` (Python reserved)
        self.from_hour = int(rest["from"] if from_ is None and "from" in rest else (from_ if from_ is not None else rest.get("from", 8)))
        self.to_hour = int(to if to is not None else rest.get("to", 20))
        self.trailing_30_minutes = trailing_30_minutes
        self.time_format = time_format
        self.stretch = stretch

    def generate(self) -> str:
        if self.stretch:
            hours = list(range(self.from_hour, self.to_hour + 1))
            header = (
                "grid.cell(\n"
                "    stroke: (bottom: regular_stroke + black),\n"
                f"    box(height: regular_height, align(horizon, [{self.i18n.t('schedule')}]))\n"
                "  )"
            )
            cells = [header]
            for hour in hours:
                pretty = self._pretty_hour(hour)
                cells.append(
                    f"grid.cell(stroke: (bottom: regular_stroke + black), align(horizon, [{pretty}]))"
                )
            return f"""grid(
  columns: 1fr,
  rows: (regular_height,) + (1fr,) * {len(hours)},
  inset: 0mm,
  {",\n  ".join(cells)}
)"""
        trailing = f",\n  {self._half_tick()}" if self.trailing_30_minutes else ""
        return f"""grid(
  columns: 1fr,
  inset: 0mm,
  grid.cell(
    stroke: (bottom: regular_stroke + black),
    box(height: regular_height, align(horizon, [{self.i18n.t("schedule")}]))
  ),
  {self._schedule_lines()}{trailing}
)"""

    def _half_tick(self) -> str:
        return "box(height: regular_height, place(bottom + left, line(length: 3mm, stroke: regular_stroke + black)))"

    def _schedule_lines(self) -> str:
        lines = []
        for hour in range(self.from_hour, self.to_hour + 1):
            pretty = self._pretty_hour(hour)
            cell = (
                "grid.cell(stroke: (bottom: regular_stroke + black), "
                f"box(height: regular_height, align(horizon, [{pretty}])))"
            )
            if self.trailing_30_minutes:
                lines.append(f"{cell}, {self._half_tick()}")
            else:
                lines.append(cell)
        return ",\n".join(lines)

    def _pretty_hour(self, hour: int) -> str:
        fmt = self.time_format
        if fmt == "%k":
            # Ruby %k: 24-hour, space-padded
            return f"{hour:2d}"
        dt = datetime(1, 1, 1, hour, 0, 0)
        return dt.strftime(fmt)
