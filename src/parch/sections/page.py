"""Page is what a section builds. Layout seats it; painters ink it."""

from dataclasses import dataclass
from typing import Literal, assert_never, overload

from parch.components import (
    AnnualGrid,
    AnnualMonth,
    BujoIndex,
    BujoKey,
    Checkoff365,
    CollectionLeaf,
    Component,
    CoverTitle,
    DotGridPad,
    EngineeringPad,
    FavoritesPage,
    FutureLogPage,
    HabitGrid,
    LinedPad,
    MeetingAgenda,
    MeetingIndex,
    MonthGrid,
    MonthlyCalendarList,
    MonthlyTaskWell,
    My100Page,
    Notes,
    Priorities,
    ProjectsBoard,
    ProjectsIndex,
    QuarterGrid,
    RapidLogPage,
    ReviewIndex,
    ReviewWeekPage,
    Schedule,
    StenoPad,
    TasksIndex,
    TasksWeekPage,
    WeekStrip,
)

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
    "engineering_front",
    "engineering_back",
    "steno",
    "dotgrid",
    "lined",
    "bujo_key",
    "bujo_index",
    "future_log",
    "monthly_log",
    "monthly_tasks",
    "rapid_log",
    "collection",
]


def check_seating(kind: PageKind, components: tuple[Component, ...]) -> None:
    """Kind and seating agree. A missing arm fails typecheck at ``assert_never``."""
    match kind:
        case "cover":
            _one(components, CoverTitle)
        case "annual":
            _one(components, AnnualGrid)
        case "favorites":
            _one(components, FavoritesPage)
        case "my_100":
            _one(components, My100Page)
        case "checkoff_365":
            _one(components, Checkoff365)
        case "projects_index":
            _one(components, ProjectsIndex)
        case "project":
            _one(components, ProjectsBoard)
        case "meetings_index":
            _one(components, MeetingIndex)
        case "meeting":
            _one(components, MeetingAgenda)
        case "tasks_index":
            _one(components, TasksIndex)
        case "task":
            _one(components, TasksWeekPage)
        case "review_index":
            _one(components, ReviewIndex)
        case "review":
            _one(components, ReviewWeekPage)
        case "quarter":
            _one(components, QuarterGrid)
        case "month":
            _one(components, MonthGrid)
        case "habits":
            _one(components, HabitGrid)
        case "weekly":
            _one(components, WeekStrip)
        case "daily":
            _types(components, (Schedule, Notes, Priorities, AnnualMonth))
        case "daily_notes":
            _one(components, Notes)
        case "engineering_front":
            _face(components, "front")
        case "engineering_back":
            _face(components, "back")
        case "steno":
            _one(components, StenoPad)
        case "dotgrid":
            _one(components, DotGridPad)
        case "lined":
            _one(components, LinedPad)
        case "bujo_key":
            _one(components, BujoKey)
        case "bujo_index":
            _one(components, BujoIndex)
        case "future_log":
            _one(components, FutureLogPage)
        case "monthly_log":
            _one(components, MonthlyCalendarList)
        case "monthly_tasks":
            _one(components, MonthlyTaskWell)
        case "rapid_log":
            _one(components, RapidLogPage)
        case "collection":
            _one(components, CollectionLeaf)
        case _:
            assert_never(kind)


def _one[T](components: tuple[Component, ...], typ: type[T]) -> T:
    if len(components) != 1 or not isinstance(components[0], typ):
        raise TypeError(f"expected one {typ.__name__}")
    return components[0]


def _types(
    components: tuple[Component, ...], types: tuple[type[Component], ...]
) -> None:
    if len(components) != len(types) or any(
        not isinstance(item, typ) for item, typ in zip(components, types, strict=True)
    ):
        expected = ", ".join(typ.__name__ for typ in types)
        raise TypeError(f"expected seating ({expected})")


def _face(components: tuple[Component, ...], face: Literal["front", "back"]) -> None:
    pad = _one(components, EngineeringPad)
    if pad.face != face:
        raise TypeError(f"expected engineering face {face}")


@dataclass(frozen=True, slots=True)
class NavItem:
    label: str
    dest: str


@dataclass(frozen=True, slots=True)
class Page:
    """Ledger row. Each ``kind`` literal accepts only its seating."""

    dest: str
    kind: PageKind
    title: str
    nav: tuple[NavItem, ...]
    components: tuple[Component, ...]

    @overload
    def __init__(
        self,
        dest: str,
        kind: Literal["cover"],
        title: str,
        nav: tuple[NavItem, ...],
        components: tuple[CoverTitle],
    ) -> None: ...

    @overload
    def __init__(
        self,
        dest: str,
        kind: Literal["annual"],
        title: str,
        nav: tuple[NavItem, ...],
        components: tuple[AnnualGrid],
    ) -> None: ...

    @overload
    def __init__(
        self,
        dest: str,
        kind: Literal["favorites"],
        title: str,
        nav: tuple[NavItem, ...],
        components: tuple[FavoritesPage],
    ) -> None: ...

    @overload
    def __init__(
        self,
        dest: str,
        kind: Literal["my_100"],
        title: str,
        nav: tuple[NavItem, ...],
        components: tuple[My100Page],
    ) -> None: ...

    @overload
    def __init__(
        self,
        dest: str,
        kind: Literal["checkoff_365"],
        title: str,
        nav: tuple[NavItem, ...],
        components: tuple[Checkoff365],
    ) -> None: ...

    @overload
    def __init__(
        self,
        dest: str,
        kind: Literal["projects_index"],
        title: str,
        nav: tuple[NavItem, ...],
        components: tuple[ProjectsIndex],
    ) -> None: ...

    @overload
    def __init__(
        self,
        dest: str,
        kind: Literal["project"],
        title: str,
        nav: tuple[NavItem, ...],
        components: tuple[ProjectsBoard],
    ) -> None: ...

    @overload
    def __init__(
        self,
        dest: str,
        kind: Literal["meetings_index"],
        title: str,
        nav: tuple[NavItem, ...],
        components: tuple[MeetingIndex],
    ) -> None: ...

    @overload
    def __init__(
        self,
        dest: str,
        kind: Literal["meeting"],
        title: str,
        nav: tuple[NavItem, ...],
        components: tuple[MeetingAgenda],
    ) -> None: ...

    @overload
    def __init__(
        self,
        dest: str,
        kind: Literal["tasks_index"],
        title: str,
        nav: tuple[NavItem, ...],
        components: tuple[TasksIndex],
    ) -> None: ...

    @overload
    def __init__(
        self,
        dest: str,
        kind: Literal["task"],
        title: str,
        nav: tuple[NavItem, ...],
        components: tuple[TasksWeekPage],
    ) -> None: ...

    @overload
    def __init__(
        self,
        dest: str,
        kind: Literal["review_index"],
        title: str,
        nav: tuple[NavItem, ...],
        components: tuple[ReviewIndex],
    ) -> None: ...

    @overload
    def __init__(
        self,
        dest: str,
        kind: Literal["review"],
        title: str,
        nav: tuple[NavItem, ...],
        components: tuple[ReviewWeekPage],
    ) -> None: ...

    @overload
    def __init__(
        self,
        dest: str,
        kind: Literal["quarter"],
        title: str,
        nav: tuple[NavItem, ...],
        components: tuple[QuarterGrid],
    ) -> None: ...

    @overload
    def __init__(
        self,
        dest: str,
        kind: Literal["month"],
        title: str,
        nav: tuple[NavItem, ...],
        components: tuple[MonthGrid],
    ) -> None: ...

    @overload
    def __init__(
        self,
        dest: str,
        kind: Literal["habits"],
        title: str,
        nav: tuple[NavItem, ...],
        components: tuple[HabitGrid],
    ) -> None: ...

    @overload
    def __init__(
        self,
        dest: str,
        kind: Literal["weekly"],
        title: str,
        nav: tuple[NavItem, ...],
        components: tuple[WeekStrip],
    ) -> None: ...

    @overload
    def __init__(
        self,
        dest: str,
        kind: Literal["daily"],
        title: str,
        nav: tuple[NavItem, ...],
        components: tuple[Schedule, Notes, Priorities, AnnualMonth],
    ) -> None: ...

    @overload
    def __init__(
        self,
        dest: str,
        kind: Literal["daily_notes"],
        title: str,
        nav: tuple[NavItem, ...],
        components: tuple[Notes],
    ) -> None: ...

    @overload
    def __init__(
        self,
        dest: str,
        kind: Literal["engineering_front"],
        title: str,
        nav: tuple[NavItem, ...],
        components: tuple[EngineeringPad],
    ) -> None: ...

    @overload
    def __init__(
        self,
        dest: str,
        kind: Literal["engineering_back"],
        title: str,
        nav: tuple[NavItem, ...],
        components: tuple[EngineeringPad],
    ) -> None: ...

    @overload
    def __init__(
        self,
        dest: str,
        kind: Literal["steno"],
        title: str,
        nav: tuple[NavItem, ...],
        components: tuple[StenoPad],
    ) -> None: ...

    @overload
    def __init__(
        self,
        dest: str,
        kind: Literal["dotgrid"],
        title: str,
        nav: tuple[NavItem, ...],
        components: tuple[DotGridPad],
    ) -> None: ...

    @overload
    def __init__(
        self,
        dest: str,
        kind: Literal["lined"],
        title: str,
        nav: tuple[NavItem, ...],
        components: tuple[LinedPad],
    ) -> None: ...

    @overload
    def __init__(
        self,
        dest: str,
        kind: Literal["bujo_key"],
        title: str,
        nav: tuple[NavItem, ...],
        components: tuple[BujoKey],
    ) -> None: ...

    @overload
    def __init__(
        self,
        dest: str,
        kind: Literal["bujo_index"],
        title: str,
        nav: tuple[NavItem, ...],
        components: tuple[BujoIndex],
    ) -> None: ...

    @overload
    def __init__(
        self,
        dest: str,
        kind: Literal["future_log"],
        title: str,
        nav: tuple[NavItem, ...],
        components: tuple[FutureLogPage],
    ) -> None: ...

    @overload
    def __init__(
        self,
        dest: str,
        kind: Literal["monthly_log"],
        title: str,
        nav: tuple[NavItem, ...],
        components: tuple[MonthlyCalendarList],
    ) -> None: ...

    @overload
    def __init__(
        self,
        dest: str,
        kind: Literal["monthly_tasks"],
        title: str,
        nav: tuple[NavItem, ...],
        components: tuple[MonthlyTaskWell],
    ) -> None: ...

    @overload
    def __init__(
        self,
        dest: str,
        kind: Literal["rapid_log"],
        title: str,
        nav: tuple[NavItem, ...],
        components: tuple[RapidLogPage],
    ) -> None: ...

    @overload
    def __init__(
        self,
        dest: str,
        kind: Literal["collection"],
        title: str,
        nav: tuple[NavItem, ...],
        components: tuple[CollectionLeaf],
    ) -> None: ...

    def __init__(
        self,
        dest: str,
        kind: PageKind,
        title: str,
        nav: tuple[NavItem, ...],
        components: tuple[Component, ...],
    ) -> None:
        check_seating(kind, components)
        object.__setattr__(self, "dest", dest)
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "nav", nav)
        object.__setattr__(self, "components", components)
