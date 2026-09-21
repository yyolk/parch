"""Single-face edge-to-edge dot-grid pad — one blank page per sheet."""

from parch.components.dot_grid import DotGridPad
from parch.sections.page import Page
from parch.spec import Spec


class DotGridPadSection:
    """Emit single-face pad pages. Joins the pad compose row — no Book."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        built: list[Page] = []
        for sheet in range(1, spec.dot_sheets + 1):
            sheets = spec.dot_sheets
            built.append(
                Page(
                    dest=spec.dest_for_dot_pad(sheet),
                    kind="dot_grid",
                    title="Dot grid",
                    nav=(),
                    components=(DotGridPad(sheet=sheet, sheets=sheets),),
                )
            )
        return built
