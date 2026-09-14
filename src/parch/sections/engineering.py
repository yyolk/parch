"""Duplex engineering / computation pad — one front + one back page per sheet."""

from parch.components.engineering import EngineeringPad
from parch.sections.page import Page
from parch.spec import Spec


class EngineeringPadSection:
    """Emit duplex pad faces. No engineering-notebook book yet — press plots this section alone."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        built: list[Page] = []
        for sheet in range(1, spec.engineering_sheets + 1):
            sheets = spec.engineering_sheets
            pad_front = EngineeringPad(face="front", sheet=sheet, sheets=sheets)
            pad_back = EngineeringPad(face="back", sheet=sheet, sheets=sheets)
            built.append(
                Page(
                    dest=spec.dest_for_engineering_pad(sheet, "front"),
                    kind="engineering_front",
                    title="Engineering",
                    nav=(),
                    components=(pad_front,),
                )
            )
            built.append(
                Page(
                    dest=spec.dest_for_engineering_pad(sheet, "back"),
                    kind="engineering_back",
                    title="Computation",
                    nav=(),
                    components=(pad_back,),
                )
            )
        return built
