"""Duplex engineering / computation pad — one front + one back page per sheet."""

from parch.components.engineering import EngineeringPad
from parch.sections.page import Page
from parch.spec import Spec


class EngineeringPadSection:
    """Emit duplex pad faces. Reused by ``EngineeringNotebook`` and pad-only press."""

    def __init__(self, spec: Spec, *, start: int = 1, count: int | None = None) -> None:
        self.spec = spec
        self.start = start
        self.count = spec.engineering_sheets if count is None else count

    def pages(self) -> list[Page]:
        spec = self.spec
        built: list[Page] = []
        for sheet in range(self.start, self.start + self.count):
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
