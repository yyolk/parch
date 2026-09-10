"""Tasks ticket index and weekly dest — data only. Painters seat the stack and template."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WeekTasks:
    """Locked weekly Tasks dest. Ticket dests set ``index_dest`` and ``number`` (header chip)."""

    year: int
    tasks: int
    carry: int
    index_dest: str = ""
    number: int = 0


@dataclass(frozen=True, slots=True)
class TaskTicket:
    """One stacked ticket on the index — stub week number + weekly Tasks dest."""

    number: int
    dest: str


@dataclass(frozen=True, slots=True)
class TasksIndex:
    """Thesis B — stacked tickets. Stub and preview link; write-in stays unlinkable."""

    year: int
    dest: str
    tickets: tuple[TaskTicket, ...]
