"""Page is what a section builds. Layout seats it; painters ink it."""

from dataclasses import dataclass
from enum import StrEnum

from parch.components import Component


class PageKind(StrEnum):
    """Closed page-kind set. The enum body is the only list.

    No parallel ``Literal[...]`` alias. Layout ``match``es members;
    ``case _: assert_never(...)`` makes a missing member a type error.
    ``list(PageKind)`` walks the same set.
    """

    COVER = "cover"
    ANNUAL = "annual"
    FAVORITES = "favorites"
    MY_100 = "my_100"
    CHECKOFF_365 = "checkoff_365"
    PROJECTS_INDEX = "projects_index"
    PROJECT = "project"
    MEETINGS_INDEX = "meetings_index"
    MEETING = "meeting"
    TASKS_INDEX = "tasks_index"
    TASK = "task"
    REVIEW_INDEX = "review_index"
    REVIEW = "review"
    QUARTER = "quarter"
    MONTH = "month"
    HABITS = "habits"
    WEEKLY = "weekly"
    DAILY = "daily"
    DAILY_NOTES = "daily_notes"
    ENGINEERING_FRONT = "engineering_front"
    ENGINEERING_BACK = "engineering_back"
    STENO = "steno"
    DOTGRID = "dotgrid"
    BUJO_KEY = "bujo_key"
    BUJO_INDEX = "bujo_index"
    FUTURE_LOG = "future_log"
    MONTHLY_LOG = "monthly_log"
    MONTHLY_TASKS = "monthly_tasks"
    RAPID_LOG = "rapid_log"
    COLLECTION = "collection"


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
