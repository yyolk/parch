"""Tasks index and weekly dest — data only. Painters seat the cover grid and well."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TaskCover:
    """One week thumbnail on the index — week label + ticks; whole cover hits the dest."""

    number: int
    dest: str


@dataclass(frozen=True, slots=True)
class TasksIndex:
    """Thesis D — mini cover grid. Each cover is a week thumbnail; the whole cover links."""

    year: int
    dest: str
    covers: tuple[TaskCover, ...]


@dataclass(frozen=True, slots=True)
class WeeklyTasks:
    """Locked weekly Tasks dest. Ticket dests set ``index_dest`` and ``number`` (header chip)."""

    year: int
    rows: int
    index_dest: str = ""
    number: int = 0
