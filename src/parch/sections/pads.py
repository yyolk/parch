"""Pad-only compose — concatenate engineering + steno sections. No cover."""

from parch.sections.engineering import EngineeringPadSection
from parch.sections.page import Page
from parch.sections.steno import StenoPadSection
from parch.spec import Spec


class PadBundleSection:
    """EngineeringPadSection pages, then StenoPadSection pages.

    Either child may be empty (sheet count 0). Press plots this section
    when either count is > 0 (year-planner pad-only path).
    """

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        return [
            *EngineeringPadSection(self.spec).pages(),
            *StenoPadSection(self.spec).pages(),
        ]
