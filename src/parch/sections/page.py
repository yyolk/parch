"""Page is what a section builds. Layout seats it; painters ink it."""

from dataclasses import dataclass
from typing import Literal

from parch.components import Component

type PageKind = Literal[
    "cover",
    "annual",
    "projects",
    "projects_index",
    "project",
    "meetings_index",
    "meeting",
    "tasks_index",
    "weekly_tasks",
    "quarter",
    "month",
    "habits",
    "weekly",
    "daily",
    "daily_notes",
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
