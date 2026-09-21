"""Page is what a section builds. Layout seats it; painters ink it.

ChromeKind stays a closed planner/bujo set. Pads share one PageKind
member (``pad``); the face is the closed PadComponent union, so a new
pad does not grow PageKind.
"""

from dataclasses import dataclass
from typing import Literal

from parch.components import Component

type ChromeKind = Literal[
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
    "bujo_key",
    "bujo_index",
    "future_log",
    "monthly_log",
    "monthly_tasks",
    "rapid_log",
    "collection",
]

type PageKind = ChromeKind | Literal["pad"]


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
