"""Engineering notebook — cover then duplex pad faces as one section walk."""

from parch.sections.cover import CoverSection
from parch.sections.engineering import EngineeringPadSection
from parch.sections.page import Page
from parch.spec import Spec


class EngineeringNotebookSection:
    """Own the two-kind walk: cover landing on sheet 1 front, then pad faces.

    Does not copy cover or pad builders — it calls the existing section classes.
    """

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        return [
            *CoverSection(
                spec,
                landing_dest=spec.dest_for_engineering_pad(1, "front"),
                eyebrow="Engineering",
                specs_lead="",
            ).pages(),
            *EngineeringPadSection(spec).pages(),
        ]
