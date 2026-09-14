"""Single-page Gregg stenographer pad — not duplex, no steno-notebook book."""

from parch.components.steno import StenoPad
from parch.sections.page import Page
from parch.spec import Spec


class StenoSection:
    """Emit identical single-sided Gregg faces. Press plots this section alone."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        built: list[Page] = []
        for sheet in range(1, spec.steno_pages + 1):
            built.append(
                Page(
                    dest=spec.dest_for_steno(sheet),
                    kind="steno",
                    title=spec.title,
                    nav=(),
                    components=(StenoPad(sheet=sheet, sheets=spec.steno_pages),),
                )
            )
        return built
