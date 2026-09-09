"""Page is what a section builds. Layout seats it; painters ink it."""

from dataclasses import dataclass

from parch.components import Component


@dataclass(frozen=True)
class NavItem:
    label: str
    dest: str


@dataclass(frozen=True)
class Page:
    dest: str
    kind: str
    title: str
    nav: tuple[NavItem, ...]
    components: tuple[Component, ...]
