"""Page is what a section builds. Layout seats it; painters ink it.

PK3: two closed unions instead of one giant PageKind Literal.
ChromeKind is planner/bujo (header + strip). PadKind is cover plus
coverless writing pads. ``Page.kind`` is their union; layout matches
chrome vs pad first, then exhausts each side. Pads do not extend the
chrome list.
"""

from dataclasses import dataclass
from typing import Literal, TypeIs, assert_never, get_args

from parch.components import Component

type ChromeKind = Literal[
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

type PadKind = Literal[
    "cover",
    "engineering_front",
    "engineering_back",
    "steno",
    "dotgrid",
]

type PageKind = ChromeKind | PadKind


def _literal_args(alias: object) -> tuple[str, ...]:
    return get_args(getattr(alias, "__value__", alias))


CHROME_KINDS: frozenset[str] = frozenset(_literal_args(ChromeKind))
PAD_KINDS: frozenset[str] = frozenset(_literal_args(PadKind))


def is_chrome_kind(kind: PageKind) -> TypeIs[ChromeKind]:
    """Narrow ``Page.kind`` to the header+strip closed set."""
    return kind in CHROME_KINDS


def is_pad_kind(kind: PageKind) -> TypeIs[PadKind]:
    """Narrow ``Page.kind`` to cover + coverless pads. Chrome stays out."""
    return kind in PAD_KINDS


def exhaust_chrome_kind(kind: ChromeKind) -> ChromeKind:
    """Closed ChromeKind identity — type checker must list every member."""
    match kind:
        case (
            "annual"
            | "favorites"
            | "my_100"
            | "checkoff_365"
            | "projects_index"
            | "project"
            | "meetings_index"
            | "meeting"
            | "tasks_index"
            | "task"
            | "review_index"
            | "review"
            | "quarter"
            | "month"
            | "habits"
            | "weekly"
            | "daily"
            | "daily_notes"
            | "bujo_key"
            | "bujo_index"
            | "future_log"
            | "monthly_log"
            | "monthly_tasks"
            | "rapid_log"
            | "collection"
        ):
            return kind
        case _:
            assert_never(kind)


def exhaust_pad_kind(kind: PadKind) -> PadKind:
    """Closed PadKind identity — type checker must list every member."""
    match kind:
        case "cover" | "engineering_front" | "engineering_back" | "steno" | "dotgrid":
            return kind
        case _:
            assert_never(kind)


@dataclass(frozen=True, slots=True)
class NavItem:
    label: str
    dest: str


@dataclass(frozen=True, slots=True)
class Page:
    dest: str
    kind: ChromeKind | PadKind
    title: str
    nav: tuple[NavItem, ...]
    components: tuple[Component, ...]
