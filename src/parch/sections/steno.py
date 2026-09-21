"""Single-face Gregg stenographer pad — one lined page per sheet."""

from parch.components.steno import StenoPad
from parch.sections.page import Page, StenoPadPage
from parch.spec import Spec


class StenoPadSection:
    """Emit single-face pad pages. No steno-notebook book yet — press plots this section alone."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        built: list[Page] = []
        for sheet in range(1, spec.steno_sheets + 1):
            sheets = spec.steno_sheets
            built.append(
                StenoPadPage(
                    dest=spec.dest_for_steno_pad(sheet),
                    title="Steno",
                    nav=(),
                    components=(StenoPad(sheet=sheet, sheets=sheets),),
                )
            )
        return built
