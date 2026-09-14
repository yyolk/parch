"""Page is what a section builds. Layout seats it; painters ink it."""

from dataclasses import dataclass, replace
from typing import Literal

from parch.components import Component

type PageKind = Literal[
    "cover",
    "annual",
    "projects_index",
    "project",
    "meetings_index",
    "meeting",
    "tasks_index",
    "task",
    "review_index",
    "review",
    "quarter",
    "month",
    "habits",
    "weekly",
    "daily",
    "daily_notes",
    "engineering_front",
    "engineering_back",
    "steno",
]


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
    outline_title: str | None = None  # first page of a section; plotter binds dest


def stamp_section_outline(section: object, pages: list[Page]) -> list[Page]:
    """Stamp ``outline_title`` on the first page (once) when ``spec.outline``."""
    title = getattr(section, "outline_title", None)
    spec = getattr(section, "spec", None)
    if not pages or title is None or spec is None or not getattr(spec, "outline", False):
        return pages
    if getattr(section, "_outline_stamped", False):
        return pages
    setattr(section, "_outline_stamped", True)
    return [replace(pages[0], outline_title=title), *pages[1:]]
