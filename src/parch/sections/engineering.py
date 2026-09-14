"""Duplex engineering / computation pad — one front + one back page per sheet."""

from parch.components.engineering import EngineeringPad
from parch.sections.page import Page
from parch.spec import Spec


def duplex_sheet(spec: Spec, sheet: int) -> tuple[Page, Page]:
    """Pure sheet expander — one front + one back for a 1-based sheet index."""
    sheets = spec.engineering_sheets
    return (
        Page(
            dest=spec.dest_for_engineering_pad(sheet, "front"),
            kind="engineering_front",
            title="Engineering",
            nav=(),
            components=(EngineeringPad(face="front", sheet=sheet, sheets=sheets),),
        ),
        Page(
            dest=spec.dest_for_engineering_pad(sheet, "back"),
            kind="engineering_back",
            title="Computation",
            nav=(),
            components=(EngineeringPad(face="back", sheet=sheet, sheets=sheets),),
        ),
    )


class EngineeringPadSection:
    """Emit duplex pad faces. Pad-only press still plots this section alone."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        built: list[Page] = []
        for sheet in range(1, self.spec.engineering_sheets + 1):
            built.extend(self.pages_for(sheet))
        return built

    def pages_for(self, sheet: int) -> list[Page]:
        """Existing section API — one duplex pair, same paint as ``duplex_sheet``."""
        return list(duplex_sheet(self.spec, sheet))
