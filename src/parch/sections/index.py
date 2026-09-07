"""Contents page (raw Typst, no MOS chrome). Optional section key ``index``."""

from parch.i18n import I18n
from parch.mos.configurator import Configurator
from parch.mos.manifest import Manifest
from parch.mos.nomad_nav import (
    CONTENTS_LABELS,
    contents_dest_id,
    contents_rows,
    nomad_topband,
)
from parch.mos.scribe_nav import INDEX_LABELS, INDEX_SKIP, scribe_hyperpaper_nav, section_dest_id
from parch.compose.page_data import PageData
from parch.sections._shared import _length_mm

_INDEX_LEFT_INSET = "4mm"
_INDEX_BOTTOM_INSET = "4mm"
_INDEX_ROW_GUTTER = "3mm"

_SKIP = INDEX_SKIP
_HUMAN = INDEX_LABELS


class Index:
    ID = "index"

    def __init__(self, section_name: str, i18n: I18n, configurator: Configurator) -> None:
        self.section_name = section_name
        self.configurator = configurator

    def register(self, manifest: Manifest) -> None:
        manifest.register_source(self.ID)

    def pages(self, manifest: Manifest) -> list[PageData]:
        return [PageData(raw_typst=True, content=self._contents(manifest))]

    def _enabled_names(self) -> list[str]:
        names: list[str] = []
        for section in self.configurator.enabled_sections():
            names.append(str(section["name"]))
        return names

    def _dest_id(self, name: str) -> str:
        if nomad_topband(self.configurator):
            return contents_dest_id(name, self.configurator)
        return section_dest_id(name, self.configurator)

    def _row(self, manifest: Manifest, name: str) -> str:
        dest = self._dest_id(name)
        label = _HUMAN[name]
        band = f"box(width: 100%, height: 100%, align(horizon + left, [{label}]))"
        if manifest.source(dest):
            band = f"padded_link(<{dest}>, {band})"
        return (
            "  grid.cell(\n"
            "    align: horizon + left,\n"
            f"    {band}\n"
            "  )"
        )


    def _row_height(self) -> str:
        """One Habits-index band: leftover column / 12 months."""
        page_h = _length_mm(self.configurator.dig_bang("document", "layout", "dimensions", "height"))
        top = _length_mm(self.configurator.dig_bang("document", "layout", "margin", "top"))
        bottom = _length_mm(self.configurator.dig_bang("document", "layout", "margin", "bottom"))
        h1 = _length_mm(self.configurator.dig_bang("document", "text", "h1"))
        available = (
            page_h - top - bottom - h1
            - _length_mm(_INDEX_BOTTOM_INSET)
            - _length_mm(_INDEX_ROW_GUTTER)
        )
        row = max(available / 12.0, 8.0)
        return f"{row:.2f}mm"

    def _nomad_row(self, manifest: Manifest, name: str, note: str | None = None) -> str:
        dest = self._dest_id(name)
        label = CONTENTS_LABELS[name]
        extra = ""
        if note:
            extra = (
                f'; h(2mm); text(size: 7.5pt, fill: luma(40%), '
                f'font: "Liberation Sans")[{note}]'
            )
        inner = (
            "grid(\n"
            "      columns: (1fr, auto),\n"
            "      rows: 1fr,\n"
            "      align: horizon,\n"
            f'      {{ text(size: 11pt, weight: "bold")[{label}]{extra} }},\n'
            '      text(size: 11pt, fill: luma(50%))[›]\n'
            "    )"
        )
        band = (
            "box(width: 100%, height: 100%, stroke: (bottom: regular_stroke), "
            f"inset: (x: 0.4mm, y: 0pt), {inner})"
        )
        if manifest.source(dest):
            band = f"padded_link(<{dest}>, {band})"
        return band

    def _contents(self, manifest: Manifest) -> str:
        if nomad_topband(self.configurator):
            return self._nomad_contents(manifest)
        rows = [
            self._row(manifest, name)
            for name in self._enabled_names()
            if name not in _SKIP and name in _HUMAN
        ]
        height = self._row_height()
        if rows:
            body = f"""grid(
  columns: 1fr,
  rows: ({", ".join([height] * len(rows))}),
  align: horizon + left,
  inset: (x: 4pt, y: 0pt),
{",\n".join(rows)}
)"""
        else:
            body = "[]"
        title = 'text(size: h1, weight: "bold")[Contents <index>]'
        if scribe_hyperpaper_nav(self.configurator):
            brand = (
                'text(size: h1, fill: white, weight: "bold")[Contents <index>]'
            )
            return f"""#grid(
  columns: 1fr,
  rows: (15mm, 1fr),
  block(
    width: 100%,
    height: 100%,
    fill: black,
    inset: (left: {_INDEX_LEFT_INSET}, right: {_INDEX_LEFT_INSET}),
    align(horizon + start, {brand})
  ),
  block(
    width: 100%,
    height: 100%,
    inset: (left: {_INDEX_LEFT_INSET}, right: {_INDEX_LEFT_INSET}, top: {_INDEX_ROW_GUTTER}, bottom: {_INDEX_BOTTOM_INSET}),
    {body}
  )
)"""
        return f"""#grid(
  columns: 1fr,
  rows: (auto, 1fr),
  row-gutter: {_INDEX_ROW_GUTTER},
  inset: (left: {_INDEX_LEFT_INSET}, bottom: {_INDEX_BOTTOM_INSET}),
  {title},
  {body}
)"""

    def _nomad_contents(self, manifest: Manifest) -> str:
        primary, more = contents_rows(self.configurator)
        year = self.configurator.start_date().year
        primary_rows = [
            self._nomad_row(manifest, name, "year glance" if name == "annual" else None)
            for name in primary
        ]
        more_rows = [
            self._nomad_row(manifest, name, "colophon" if name == "colophon" else None)
            for name in more
        ]
        n_primary = len(primary_rows)
        n_more = len(more_rows)
        n = n_primary + n_more
        primary_cells = ",\n      ".join(primary_rows) if primary_rows else "[]"
        more_cells = ",\n      ".join(more_rows) if more_rows else "[]"
        brand = 'text(fill: white, size: 14pt, weight: "bold")[Contents <index>]'
        year_cell = (
            f'text(fill: white, size: 9pt, weight: "bold", '
            f'font: "Liberation Sans")[{year}]'
        )
        more_head = (
            'text(size: 6.5pt, tracking: 0.9pt, fill: luma(45%), '
            'font: "Liberation Sans", weight: "bold")[MORE]'
        )
        if not n:
            rows = "auto"
            body_cells = "[]"
        else:
            rows = f"(row-h,) * {n_primary} + (gap-h,) + (row-h,) * {n_more}"
            body_cells = (
                f"{primary_cells},\n"
                f"      align(bottom, pad(bottom: 1mm, {more_head})),\n"
                f"      {more_cells}"
            )
        return f"""#set text(font: "Libertinus Serif")
#set par(spacing: 0pt)
#block(width: 100%, height: 100%, {{
  grid(
    columns: 1fr,
    rows: (14mm, 2mm, 1fr),
    block(width: 100%, height: 100%, fill: black, inset: (x: 2mm), {{
      grid(
        columns: (1fr, auto),
        rows: 1fr,
        align: horizon,
        {brand},
        {year_cell},
      )
    }}),
    [],
    layout(size => {{
      let gap-h = 5mm
      let n = {max(n, 1)}
      let avail = size.height - gap-h
      let natural = avail / n
      let row-h = if (9mm * n) <= avail {{ calc.max(9mm, natural) }} else {{ natural }}
      grid(
        rows: {rows},
        row-gutter: 0pt,
        {body_cells},
      )
    }}),
  )
}})"""
