"""Plain cover page (raw Typst, no MOS chrome)."""

from parch.i18n import I18n
from parch.mos.configurator import Configurator
from parch.mos.nomad_nav import nomad_topband
from parch.mos.scribe_nav import scribe_hyperpaper_nav
from parch.compose.page_data import PageData
from parch.sections.annual import Annual
from parch.sections.index import Index


def _escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace("#", "\\#")
        .replace("[", "\\[")
        .replace("]", "\\]")
    )


class CoverPlain:
    def __init__(self, section_name: str, i18n: I18n, configurator: Configurator, name: str, font_size: str) -> None:
        self.section_name = section_name
        self.configurator = configurator
        self.name = name
        self.font_size = font_size

    def register(self, _manifest) -> None:
        return None

    def pages(self, manifest) -> list[PageData]:
        if nomad_topband(self.configurator):
            return [
                PageData(
                    content=self._nomad_cover(manifest),
                    page_id="cover",
                    heading=False,
                    strip="none",
                )
            ]
        return [PageData(raw_typst=True, content=self._cover(manifest))]

    def _lines(self) -> list[str]:
        return [line for line in str(self.name).split("\n") if line.strip()]

    def _dest(self, manifest) -> str | None:
        """Contents if that source is on, else Annual."""
        if manifest is None:
            return None
        if manifest.source(Index.ID):
            return Index.ID
        if manifest.source(Annual.ID):
            return Annual.ID
        return None

    def _year(self, size: str, year: str, dest: str | None, manifest) -> str:
        """Year as a door when dest is registered."""
        if dest is None:
            return f"text(size: {size})[{year}]"
        return f"text(size: {size}, {manifest.link_or_content(dest, year)})"

    def _cover(self, manifest) -> str:
        lines = [_escape(line) for line in self._lines()]
        size = self.font_size
        dest = self._dest(manifest)
        if not lines:
            body = "[]"
        elif len(lines) == 1:
            body = self._year(size, lines[0], dest, manifest)
        else:
            parts = [self._year(size, lines[0], dest, manifest)]
            parts.extend(f"text(size: {size} * 0.45)[{line}]" for line in lines[1:])
            body = f"stack(spacing: {size} * 0.12, {', '.join(parts)})"
        if scribe_hyperpaper_nav(self.configurator):
            brand = 'text(size: h1, fill: white, weight: "bold")[parch]'
            return f"""#grid(
  columns: 1fr,
  rows: (15mm, 1fr, 2fr),
  block(
    width: 100%,
    height: 100%,
    fill: black,
    inset: (left: 4mm, right: 4mm),
    align(horizon + start, {brand})
  ),
  align(center + horizon, {body}),
  [],
)"""
        return f"""#grid(
  columns: 1fr,
  rows: (1fr, 2fr),
  align: center + horizon,
  {body}
)"""

    def _nomad_cover(self, manifest) -> str:
        dest = self._dest(manifest)
        year_label = str(self.configurator.start_date().year)
        year = self._year(
            '48pt, weight: "bold", tracking: 1.5pt',
            year_label,
            dest,
            manifest,
        )
        # page-shell already reserved toolbar + bezel. Extra inset matches
        # locked 00-cover (x: bezel+2mm, top: 8mm, bottom: bezel+4mm).
        return f"""block(
  width: 100%,
  height: 100%,
  inset: (x: 2mm, top: 8mm, bottom: 4mm),
  {{
    v(1fr)
    align(center, {{
      {year}
      v(4mm)
      box(width: 42mm, {{
        box(width: 100%, height: 0.7pt, fill: black)
        v(0.7mm)
        box(width: 100%, height: 0.35pt, fill: luma(25%))
      }})
    }})
    v(1.15fr)
    align(center, text(size: 7.5pt, font: "Liberation Sans", fill: luma(45%))[Supernote Nomad])
  }},
)"""
