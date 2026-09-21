"""Single-face full-bleed dot-grid pad — one page per sheet."""

from parch.components.dotgrid import DotGridPad
from parch.sections.page import Page
from parch.spec import Spec


class DotGridPadSection:
    """Emit full-bleed pad pages. No dot-grid-notebook book yet — press plots this section."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        built: list[Page] = []
        for sheet in range(1, spec.dotgrid_sheets + 1):
            sheets = spec.dotgrid_sheets
            built.append(
                Page(
                    dest=spec.dest_for_dotgrid_pad(sheet),
                    kind="dot_grid",
                    title="Dot grid",
                    nav=(),
                    components=(DotGridPad(sheet=sheet, sheets=sheets),),
                )
            )
        return built
