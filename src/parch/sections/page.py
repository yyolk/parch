"""Page is what a section builds. Layout seats it; painters ink it."""

from dataclasses import dataclass

from parch.sections.kind import PageKind
from parch.sections.seating import Seating, seating_view

__all__ = ["NavItem", "Page", "PageKind"]


@dataclass(frozen=True, slots=True)
class NavItem:
    label: str
    dest: str


@dataclass(frozen=True, slots=True)
class Page:
    """Ledger row. ``kind`` is the seating's label, not a stored field."""

    dest: str
    title: str
    nav: tuple[NavItem, ...]
    components: Seating

    @property
    def kind(self) -> PageKind:
        """Label derived from ``components``. A mismatched kind cannot be stored."""
        return seating_view(self.components, self.dest).kind
