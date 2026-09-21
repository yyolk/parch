"""Single-face edge-to-edge dot-grid page — one sheet per dest.

Thinnest pad-style wrapper: Spec sheet count → ``Page`` + ``DotGrid``.
No header, nav, or Book. Press plots this section when
``dot_grid_sheets > 0``.
"""

from parch.components.dot_grid import DotGrid
from parch.sections.page import Page
from parch.spec import Spec


class DotGridSection:
    """Emit pad-only dot-grid pages. Same shape as ``StenoPadSection``."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        built: list[Page] = []
        for sheet in range(1, spec.dot_grid_sheets + 1):
            built.append(
                Page(
                    dest=spec.dest_for_dot_grid(sheet),
                    kind="dot_grid",
                    title="Dot grid",
                    nav=(),
                    components=(DotGrid(sheet=sheet, sheets=spec.dot_grid_sheets),),
                )
            )
        return built
