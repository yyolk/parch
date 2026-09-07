"""Contents page (raw Typst, no MOS chrome). Optional section key ``index``."""

from parch.i18n import I18n
from parch.mos.configurator import Configurator
from parch.mos.manifest import Manifest
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

    def _contents(self, manifest: Manifest) -> str:
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
