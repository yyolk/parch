"""Single-face Gregg stenographer pad — one lined page per sheet."""

from parch.components.steno import StenoPad
from parch.sections.page import Page
from parch.spec import Spec


class StenoPadSection:
    """Emit single-face pad pages. No steno-notebook book yet — press plots this section alone."""

    def __init__(self, spec: Spec, *, start: int = 1, count: int | None = None) -> None:
        self.spec = spec
        self.start = start
        self.count = spec.steno_sheets if count is None else count

    def pages(self) -> list[Page]:
        spec = self.spec
        built: list[Page] = []
        for sheet in range(self.start, self.start + self.count):
            sheets = spec.steno_sheets
            built.append(
                Page(
                    dest=spec.dest_for_steno_pad(sheet),
                    kind="steno",
                    title="Steno",
                    nav=(),
                    components=(StenoPad(sheet=sheet, sheets=sheets),),
                )
            )
        return built
