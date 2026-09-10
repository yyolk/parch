"""Weekly Tasks dest, index, and week slots — data only. Painters seat them."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class TaskWeek:
    """One ISO week on the index — stub + weekly Tasks dest."""

    iso_year: int
    iso_week: int
    monday: date
    sunday: date
    dest: str


@dataclass(frozen=True, slots=True)
class TasksIndex:
    """Thesis E — featured this-week panel + compact linked list of other weeks."""

    year: int
    dest: str
    featured: TaskWeek
    entries: tuple[TaskWeek, ...]
    preview: int = 3


@dataclass(frozen=True, slots=True)
class WeeklyTasks:
    """Locked weekly Tasks dest — checklist over flex notes."""

    year: int
    iso_week: int
    monday: date
    sunday: date
    tasks: int
    dest: str = ""
    index_dest: str = ""
