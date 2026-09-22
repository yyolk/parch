"""Page is what a section builds. Layout seats it; painters ink it."""

from dataclasses import dataclass

from parch.components import Component, PageComponent, as_page_component

__all__ = ["NavItem", "Page"]


@dataclass(frozen=True, slots=True)
class NavItem:
    label: str
    dest: str


@dataclass(frozen=True, slots=True)
class Page:
    """A pressed leaf. ``kind`` is an outline/progress label only.

    Layout paints by matching ``lead`` against the closed chrome/well
    component unions — not a PageKind string list.
    """

    dest: str
    kind: str
    title: str
    nav: tuple[NavItem, ...]
    components: tuple[Component, ...]

    @property
    def lead(self) -> PageComponent:
        """First page-lead component. Nested Component members raise."""
        if not self.components:
            raise TypeError(f"{self.dest} has no components")
        return as_page_component(self.components[0])
