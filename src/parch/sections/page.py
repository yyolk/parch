"""Page is what a section builds. Layout seats it; painters ink it."""

from dataclasses import dataclass

from parch.components import Component
from parch.kinds import PageKind


@dataclass(frozen=True, slots=True)
class NavItem:
    label: str
    dest: str


@dataclass(frozen=True, slots=True)
class Page:
    dest: str
    kind: PageKind
    title: str
    nav: tuple[NavItem, ...]
    components: tuple[Component, ...]
