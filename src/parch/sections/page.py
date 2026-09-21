"""Page is what a section builds. Layout seats it; painters ink it."""

from dataclasses import dataclass
from typing import Literal

from parch.components import Component

type PageKind = Literal[
    "cover",
    "annual",
    "favorites",
    "my_100",
    "checkoff_365",
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
    "dot_grid",
    "engineering_front",
    "engineering_back",
    "steno",
    "bujo_key",
    "bujo_index",
    "future_log",
    "monthly_log",
    "monthly_tasks",
    "rapid_log",
    "collection",
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
