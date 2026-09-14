"""Duplex engineering computation pad — one sheet, two PDF pages."""

from parch.components.engineering import EngineeringPad
from parch.sections.page import Page
from parch.spec import Spec


class EngineeringPadSection:
    """Front (header + blank well) then back (5×5 grid). Not a notebook."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        return [
            Page(
                dest=spec.engineering_front_dest,
                kind="engineering_front",
                title="Engineering",
                nav=(),
                components=(EngineeringPad(face="front", year=spec.year),),
            ),
            Page(
                dest=spec.engineering_back_dest,
                kind="engineering_back",
                title="Engineering",
                nav=(),
                components=(EngineeringPad(face="back", year=spec.year),),
            ),
        ]
