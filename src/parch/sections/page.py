"""Page is what a section builds. Layout seats it; painters ink it."""

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
    "bujo_key",
    "bujo_index",
    "future_log",
    "monthly_log",
    "monthly_tasks",
    "rapid_log",
    "collection",
    "favorites",
    "my_100",
    "days_365",
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
