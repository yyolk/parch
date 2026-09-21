"""Coverless clone-dot notebook — one full-bleed page per sheet."""

from parch.components.dot_grid import DotGridSheet
from parch.sections.page import Page
from parch.spec import Spec


class DotGridSection:
    """Emit single-face dot-grid pages. Used by the ``dot-grid`` book."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        built: list[Page] = []
        for sheet in range(1, spec.dot_grid_sheets + 1):
            sheets = spec.dot_grid_sheets
            built.append(
                Page(
                    dest=spec.dest_for_dot_grid(sheet),
                    kind="dot_grid",
                    title="Dot grid",
                    nav=(),
                    components=(DotGridSheet(sheet=sheet, sheets=sheets),),
                )
            )
        return built
