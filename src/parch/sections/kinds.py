"""Sealed page-kind catalog. Subclasses register; the union must match or import fails."""

from typing import ClassVar


class Kind:
    """Closed page kind. ``tag=`` on the class is the only wire label."""

    tag: ClassVar[str]

    def __init_subclass__(cls, *, tag: str, **kwargs: object) -> None:
        """Register a direct subclass until ``_seal`` freezes the catalog."""
        super().__init_subclass__(**kwargs)
        if cls.__bases__ != (Kind,):
            raise TypeError(f"{cls.__name__} must subclass Kind directly")
        if _sealed:
            raise TypeError(f"{cls.__name__} cannot extend a sealed page kind")
        if not isinstance(tag, str) or not tag.isidentifier():
            raise TypeError(f"{cls.__name__} tag must be an identifier")
        if any(existing.tag == tag for existing in _members):
            raise TypeError(f"duplicate page kind tag {tag!r}")
        cls.tag = tag
        _members.append(cls)

    def __eq__(self, other: object) -> bool:
        """Same class, or the tag string, so ``page.kind == "cover"`` still holds."""
        if isinstance(other, Kind):
            return type(other) is type(self)
        if isinstance(other, str):
            return other == type(self).tag
        return NotImplemented

    def __hash__(self) -> int:
        """Hash as the tag so a kind can key a dict looked up by that string."""
        return hash(type(self).tag)

    def __str__(self) -> str:
        """Tag label for progress and outline."""
        return type(self).tag

    def __repr__(self) -> str:
        """Class name, since instances of one kind are interchangeable."""
        return f"{type(self).__name__}()"


_members: list[type[Kind]] = []
_sealed = False


class Cover(Kind, tag="cover"):
    pass


class Annual(Kind, tag="annual"):
    pass


class Favorites(Kind, tag="favorites"):
    pass


class My100(Kind, tag="my_100"):
    pass


class Checkoff365(Kind, tag="checkoff_365"):
    pass


class ProjectsIndex(Kind, tag="projects_index"):
    pass


class Project(Kind, tag="project"):
    pass


class MeetingsIndex(Kind, tag="meetings_index"):
    pass


class Meeting(Kind, tag="meeting"):
    pass


class TasksIndex(Kind, tag="tasks_index"):
    pass


class Task(Kind, tag="task"):
    pass


class ReviewIndex(Kind, tag="review_index"):
    pass


class Review(Kind, tag="review"):
    pass


class Quarter(Kind, tag="quarter"):
    pass


class Month(Kind, tag="month"):
    pass


class Habits(Kind, tag="habits"):
    pass


class Weekly(Kind, tag="weekly"):
    pass


class Daily(Kind, tag="daily"):
    pass


class DailyNotes(Kind, tag="daily_notes"):
    pass


class EngineeringFront(Kind, tag="engineering_front"):
    pass


class EngineeringBack(Kind, tag="engineering_back"):
    pass


class Steno(Kind, tag="steno"):
    pass


class Dotgrid(Kind, tag="dotgrid"):
    pass


class Lined(Kind, tag="lined"):
    pass


class BujoKey(Kind, tag="bujo_key"):
    pass


class BujoIndex(Kind, tag="bujo_index"):
    pass


class FutureLog(Kind, tag="future_log"):
    pass


class MonthlyLog(Kind, tag="monthly_log"):
    pass


class MonthlyTasks(Kind, tag="monthly_tasks"):
    pass


class RapidLog(Kind, tag="rapid_log"):
    pass


class Collection(Kind, tag="collection"):
    pass


type PageKind = (
    Cover
    | Annual
    | Favorites
    | My100
    | Checkoff365
    | ProjectsIndex
    | Project
    | MeetingsIndex
    | Meeting
    | TasksIndex
    | Task
    | ReviewIndex
    | Review
    | Quarter
    | Month
    | Habits
    | Weekly
    | Daily
    | DailyNotes
    | EngineeringFront
    | EngineeringBack
    | Steno
    | Dotgrid
    | Lined
    | BujoKey
    | BujoIndex
    | FutureLog
    | MonthlyLog
    | MonthlyTasks
    | RapidLog
    | Collection
)


def _seal() -> tuple[type[Kind], ...]:
    """Freeze the catalog. The explicit union must name every registered class."""
    global _sealed
    declared = frozenset(PageKind.__value__.__args__)
    registered = frozenset(_members)
    if declared != registered:
        missing = sorted(cls.__name__ for cls in registered - declared)
        extra = sorted(
            getattr(cls, "__name__", repr(cls)) for cls in declared - registered
        )
        raise TypeError(f"page kind seal mismatch missing={missing} extra={extra}")
    _sealed = True
    return tuple(_members)


KIND_CATALOG: tuple[type[Kind], ...] = _seal()
