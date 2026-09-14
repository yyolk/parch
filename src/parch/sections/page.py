"""Page is what a section builds. Layout seats it; painters ink it."""

from collections.abc import Iterable
from dataclasses import dataclass
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


def outline_section(kind: PageKind) -> str | None:
    """Reader-outline family for ``kind``; cover is omitted."""
    match kind:
        case "cover":
            return None
        case "projects_index" | "project":
            return "projects"
        case "meetings_index" | "meeting":
            return "meetings"
        case "tasks_index" | "task":
            return "tasks"
        case "review_index" | "review":
            return "review"
        case "engineering_front" | "engineering_back":
            return "engineering"
        case _:
            return kind


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


def outline_starts(pages: Iterable[Page]) -> list[Page]:
    """First page of each non-cover section (flat list, no hierarchy)."""
    seen: set[str] = set()
    starts: list[Page] = []
    for page in pages:
        key = outline_section(page.kind)
        if key is None or key in seen:
            continue
        seen.add(key)
        starts.append(page)
    return starts
