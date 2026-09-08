"""Habits index (raw Typst) and per-month tracker grids (MOS chrome)."""

from parch.calendar import walk
from parch.calendar.day import Day
from parch.calendar.month import Month
from parch.i18n import I18n
from parch.mos.configurator import Configurator
from parch.mos.manifest import Manifest
from parch.mos.contents_mark import body_size_token, heading_height_token, trail_heading
from parch.compose.page_data import HeadingMark, PageData
from parch.mos.nomad_nav import nomad_topband

_INDEX_LEFT_INSET = "4mm"
_INDEX_BOTTOM_INSET = "4mm"
_INDEX_ROW_GUTTER = "3mm"
_HEADER_ROW = "regular_height"
_BOX = "grid.cell(stroke: regular_stroke, [])"


class Habits:
    ID = "habits"
    DEFAULT_COLUMNS = 4
    NOMAD_COLUMNS = 5

    def __init__(
        self,
        section_name: str,
        i18n: I18n,
        configurator: Configurator,
        habit_columns: int = DEFAULT_COLUMNS,
        names: list[str] | None = None,
    ) -> None:
        self.section_name = section_name
        self.i18n = i18n
        self.configurator = configurator
        columns = int(habit_columns)
        if nomad_topband(configurator):
            columns = max(columns, self.NOMAD_COLUMNS)
        self.habit_columns = columns
        self.names = list(names) if names else []

    def register(self, manifest: Manifest) -> None:
        manifest.register_source(self.ID)
        for month in self._range():
            manifest.register_source(self.month_id(month))

    @staticmethod
    def month_id(month: Month) -> str:
        return f"habits-{month.name}"

    def pages(self, manifest: Manifest) -> list[PageData]:
        months = list(self._range())
        nomad = nomad_topband(self.configurator)
        year = (
            f'text(size: 7.5pt, weight: "bold")[{self.configurator.start_date().year}]'
            if nomad
            else None
        )
        if nomad:
            out = [
                PageData(
                    title=f'text(size: h1)[{self.i18n.t("habits")} <{self.ID}>]',
                    content=self._index_body(manifest, months),
                    page_id=self.ID,
                    heading_mark=HeadingMark.TRAIL,
                    year=year,
                )
            ]
        else:
            out = [PageData(raw_typst=True, content=self._index(manifest, months))]
        for month in months:
            page_id = self.month_id(month)
            out.append(
                PageData(
                    title=self._month_title(manifest, month),
                    content=self._month_grid(manifest, month),
                    page_id=page_id,
                    highlight_months=[month],
                    highlight_quarters=[month.quarter()],
                    month_link_id=self.month_id,
                    show_quarters=False,
                    nav_links=[],
                    heading_mark=HeadingMark.TRAIL,
                    year=year,
                )
            )
        return out

    def _range(self):
        return walk(self.configurator.start_date().month(), self.configurator.end_date().month())

    def _heading(self, manifest: Manifest, habits_cell: str) -> str:
        return trail_heading(
            manifest,
            heading_height_token(self.configurator),
            f"text(size: h1, {habits_cell})",
            body_size_token(self.configurator),
            edge=HeadingMark.FOLLOW,
        )

    def _index_body(self, manifest: Manifest, months: list[Month]) -> str:
        n = len(months)
        if not n:
            return "[]"
        rows = []
        for month in months:
            hid = self.month_id(month)
            name = self.i18n.t(f"months.full.{month.name}")
            band = (
                "box(width: 100%, height: 100%, "
                f"align(horizon + left, [{name}]))"
            )
            if manifest.source(hid):
                # Link wraps the full-size box so the PDF annotation
                # is the 1fr cell, not the padded month word.
                band = f"padded_link(<{hid}>, {band})"
            rows.append(
                "  grid.cell(\n"
                "    align: horizon + left,\n"
                f"    {band}\n"
                "  )"
            )
        return f"""box(
  width: 100%,
  height: 100%,
  grid(
    columns: 1fr,
    rows: ({", ".join(["1fr"] * n)}),
    align: horizon + left,
    inset: (x: 4pt, y: 0pt),
{",\n".join(rows)}
  )
)"""

    def _index(self, manifest: Manifest, months: list[Month]) -> str:
        body = self._index_body(manifest, months)
        habits_cell = f"[{self.i18n.t('habits')} <{self.ID}>]"
        return f"""#grid(
  columns: 1fr,
  rows: (auto, 1fr),
  row-gutter: {_INDEX_ROW_GUTTER},
  inset: (left: {_INDEX_LEFT_INSET}, bottom: {_INDEX_BOTTOM_INSET}),
  {self._heading(manifest, habits_cell)},
  {body}
)"""

    def _month_title(self, manifest: Manifest, month: Month) -> str:
        full = self.i18n.t(f"months.full.{month.name}")
        page_id = self.month_id(month)
        if nomad_topband(self.configurator):
            return (
                f'text(size: 10pt, weight: "bold")'
                f'[{self.i18n.t("habits")}  ·  {full}<{page_id}>]'
            )
        habits_cell = manifest.link_or_content(self.ID, self.i18n.t("habits"))
        return f"""box(
  width: 90%,
  inset: (bottom: 0.25em),
  align(horizon + left, stack(
    dir: ltr,
    spacing: 0.5em,
    text(size: h1, bottom-edge: "descender", {habits_cell}),
    text(size: h1, bottom-edge: "descender")[{full}<{page_id}>]
  ))
)"""

    def _month_grid(self, manifest: Manifest, month: Month) -> str:
        if nomad_topband(self.configurator):
            return self._nomad_month_grid(manifest, month)
        days = list(walk(month.day, month.day.end_of_month()))
        n_habits = self.habit_columns
        cols = ", ".join(["auto"] + ["1fr"] * n_habits)
        row_sizes = [_HEADER_ROW]
        padded = (list(self.names) + [""] * n_habits)[:n_habits]
        headers = ["[]"] + [_habit_header(name) for name in padded]
        cells = [", ".join(headers)]
        for day in days:
            row = [self._date_label(manifest, day)]
            row.extend([_BOX] * n_habits)
            cells.append(", ".join(row))
            row_sizes.append("1fr")
        rows = ", ".join(row_sizes)
        return f"""grid(
  columns: ({cols}),
  rows: ({rows}),
  align: horizon,
  inset: 0pt,
  column-gutter: 0pt,
  row-gutter: 0pt,
  {",\n  ".join(cells)}
)"""

    def _nomad_month_grid(self, manifest: Manifest, month: Month) -> str:
        """Locked empty habits: Day + underline headers, 1…31, tick squares."""
        days = list(walk(month.day, month.day.end_of_month()))
        n_habits = self.habit_columns
        padded = (list(self.names) + [None] * n_habits)[:n_habits]
        headers = [_nomad_habit_header(name) for name in padded]
        day_rows = [self._nomad_day_row(manifest, day, n_habits) for day in days]
        return f"""box(width: 100%, height: 100%, {{
  grid(
    rows: (5.5mm, 1fr),
    row-gutter: 0.8mm,
    grid(
      columns: (8mm,) + (1fr,) * {n_habits},
      column-gutter: 0.8mm,
      rows: (1fr,),
      align(horizon, text(size: 6.5pt, fill: luma(45%), font: "Liberation Sans")[Day]),
      {", ".join(headers)},
    ),
    layout(size => {{
      let n = {len(days)}
      let row-h = size.height / n
      grid(
        rows: (row-h,) * n,
        row-gutter: 0pt,
        {", ".join(day_rows)},
      )
    }}),
  )
}})"""

    def _nomad_day_row(self, manifest: Manifest, day: Day, n_habits: int) -> str:
        linked = manifest.link_or_content(day.id, str(day.month_day))
        ticks = ", ".join(
            ["align(center + horizon, square(size: 0.8em, stroke: hair + ink))"]
            * n_habits
        )
        return (
            "grid(\n"
            f"        columns: (8mm,) + (1fr,) * {n_habits},\n"
            "        column-gutter: 0.8mm,\n"
            "        rows: (1fr,),\n"
            "        align: (horizon, horizon),\n"
            f'        align(right + horizon, pad(right: 1mm, text(size: 6.5pt, font: "Liberation Sans", fill: luma(30%), {linked}))),\n'
            f"        {ticks},\n"
            "      )"
        )

    def _date_label(self, manifest: Manifest, day: Day) -> str:
        short = self.i18n.t(f"weekday.short.{day.weekday_name}")
        linked = manifest.link_or_content(day.id, f"{short} {day.month_day}")
        return f"grid.cell(inset: (x: 2mm), align: horizon + right, [#{linked}])"


def _escape_typst(text: str) -> str:
    """Escape Typst specials so a habit name cannot break the document."""
    return (
        text.replace("\\", "\\\\")
        .replace("#", "\\#")
        .replace("[", "\\[")
        .replace("]", "\\]")
    )


def _habit_header(name: str) -> str:
    if not name:
        return _BOX
    label = _escape_typst(name)
    return (
        "grid.cell(\n"
        "  inset: 0pt,\n"
        "  stroke: regular_stroke,\n"
        "  align(center + horizon, text["
        + label
        + "])\n"
        ")"
    )


def _nomad_habit_header(name: str | None) -> str:
    if not name:
        return "align(horizon, line(length: 100%, stroke: hair + ink))"
    label = _escape_typst(name)
    return (
        f'align(center + horizon, text(size: 6.5pt, weight: "bold", '
        f'font: "Liberation Sans")[{label}])'
    )
