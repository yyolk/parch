"""Single-sided Gregg / stenographer pad — one PDF page per sheet, no verso."""

from parch.components.steno import StenoPad
from parch.sections.page import Page
from parch.spec import Spec


class StenoPadSection:
    """Emit pad sheets. No steno-notebook book — press plots this section alone."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        steno = spec.steno
        built: list[Page] = []
        for sheet in range(1, steno.pages + 1):
            built.append(
                Page(
                    dest=spec.dest_for_steno(sheet),
                    kind="steno",
                    title="Steno",
                    nav=(),
                    components=(
                        StenoPad(
                            line_pitch_mm=steno.line_pitch_mm,
                            center_rule=steno.center_rule,
                            sheet=sheet,
                            sheets=steno.pages,
                        ),
                    ),
                )
            )
        return built
