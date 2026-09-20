"""Pad-only compose — concatenate engineering + steno pages. No cover."""

from parch.sections.engineering import EngineeringPadSection
from parch.sections.page import Page
from parch.sections.steno import StenoPadSection
from parch.spec import Spec


def pad_pages(spec: Spec) -> list[Page]:
    """EngineeringPadSection pages, then StenoPadSection pages.

    Either child may be empty (sheet count 0). Press plots this
    ledger when either count is > 0 (year-planner pad-only path).
    """
    return [
        *EngineeringPadSection(spec).pages(),
        *StenoPadSection(spec).pages(),
    ]
