"""Page is what a section builds. Layout seats it; painters ink it.

PK1: closed union of frozen page dataclasses. Layout ``match``es on type
and ``assert_never``s the remainder — no hand-maintained ``PageKind``
``Literal`` list, no import-time registry.
"""

from dataclasses import dataclass
from typing import ClassVar

from parch.components import Component


@dataclass(frozen=True, slots=True)
class NavItem:
    label: str
    dest: str


@dataclass(frozen=True, slots=True)
class _Page:
    dest: str
    title: str
    nav: tuple[NavItem, ...]
    components: tuple[Component, ...]


@dataclass(frozen=True, slots=True)
class CoverPage(_Page):
    kind: ClassVar[str] = "cover"


@dataclass(frozen=True, slots=True)
class AnnualPage(_Page):
    kind: ClassVar[str] = "annual"


@dataclass(frozen=True, slots=True)
class FavoritesHubPage(_Page):
    kind: ClassVar[str] = "favorites"


@dataclass(frozen=True, slots=True)
class My100HubPage(_Page):
    kind: ClassVar[str] = "my_100"


@dataclass(frozen=True, slots=True)
class Checkoff365Page(_Page):
    kind: ClassVar[str] = "checkoff_365"


@dataclass(frozen=True, slots=True)
class ProjectsIndexPage(_Page):
    kind: ClassVar[str] = "projects_index"


@dataclass(frozen=True, slots=True)
class ProjectPage(_Page):
    kind: ClassVar[str] = "project"


@dataclass(frozen=True, slots=True)
class MeetingsIndexPage(_Page):
    kind: ClassVar[str] = "meetings_index"


@dataclass(frozen=True, slots=True)
class MeetingPage(_Page):
    kind: ClassVar[str] = "meeting"


@dataclass(frozen=True, slots=True)
class TasksIndexPage(_Page):
    kind: ClassVar[str] = "tasks_index"


@dataclass(frozen=True, slots=True)
class TaskPage(_Page):
    kind: ClassVar[str] = "task"


@dataclass(frozen=True, slots=True)
class ReviewIndexPage(_Page):
    kind: ClassVar[str] = "review_index"


@dataclass(frozen=True, slots=True)
class ReviewPage(_Page):
    kind: ClassVar[str] = "review"


@dataclass(frozen=True, slots=True)
class QuarterPage(_Page):
    kind: ClassVar[str] = "quarter"


@dataclass(frozen=True, slots=True)
class MonthPage(_Page):
    kind: ClassVar[str] = "month"


@dataclass(frozen=True, slots=True)
class HabitsPage(_Page):
    kind: ClassVar[str] = "habits"


@dataclass(frozen=True, slots=True)
class WeeklyPage(_Page):
    kind: ClassVar[str] = "weekly"


@dataclass(frozen=True, slots=True)
class DailyPage(_Page):
    kind: ClassVar[str] = "daily"


@dataclass(frozen=True, slots=True)
class DailyNotesPage(_Page):
    kind: ClassVar[str] = "daily_notes"


@dataclass(frozen=True, slots=True)
class EngineeringFrontPage(_Page):
    kind: ClassVar[str] = "engineering_front"


@dataclass(frozen=True, slots=True)
class EngineeringBackPage(_Page):
    kind: ClassVar[str] = "engineering_back"


@dataclass(frozen=True, slots=True)
class StenoPadPage(_Page):
    kind: ClassVar[str] = "steno"


@dataclass(frozen=True, slots=True)
class DotgridPage(_Page):
    kind: ClassVar[str] = "dotgrid"


@dataclass(frozen=True, slots=True)
class BujoKeyPage(_Page):
    kind: ClassVar[str] = "bujo_key"


@dataclass(frozen=True, slots=True)
class BujoIndexPage(_Page):
    kind: ClassVar[str] = "bujo_index"


@dataclass(frozen=True, slots=True)
class FutureLogHubPage(_Page):
    kind: ClassVar[str] = "future_log"


@dataclass(frozen=True, slots=True)
class MonthlyLogPage(_Page):
    kind: ClassVar[str] = "monthly_log"


@dataclass(frozen=True, slots=True)
class MonthlyTasksPage(_Page):
    kind: ClassVar[str] = "monthly_tasks"


@dataclass(frozen=True, slots=True)
class RapidLogHubPage(_Page):
    kind: ClassVar[str] = "rapid_log"


@dataclass(frozen=True, slots=True)
class CollectionPage(_Page):
    kind: ClassVar[str] = "collection"


type FullBleedPage = (
    CoverPage | EngineeringFrontPage | EngineeringBackPage | StenoPadPage | DotgridPage
)

type HeaderPage = (
    AnnualPage
    | FavoritesHubPage
    | My100HubPage
    | Checkoff365Page
    | ProjectsIndexPage
    | ProjectPage
    | MeetingsIndexPage
    | MeetingPage
    | TasksIndexPage
    | TaskPage
    | ReviewIndexPage
    | ReviewPage
    | QuarterPage
    | MonthPage
    | HabitsPage
    | WeeklyPage
    | DailyPage
    | DailyNotesPage
    | BujoKeyPage
    | BujoIndexPage
    | FutureLogHubPage
    | MonthlyLogPage
    | MonthlyTasksPage
    | RapidLogHubPage
    | CollectionPage
)

type Page = FullBleedPage | HeaderPage
