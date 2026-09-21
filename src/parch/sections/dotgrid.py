"""Single-face full-bleed dot-grid pad — one page per sheet."""

from parch.components.dotgrid import DotGridPad
from parch.sections.page import Page
from parch.spec import Spec


class DotGridSection:
    """Emit single-face pad pages. Press plots this section when ``dotgrid_sheets > 0``."""

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
                    kind="dotgrid",
                    title="Dot grid",
                    nav=(),
                    components=(DotGridPad(sheet=sheet, sheets=sheets),),
                )
            )
        return built
