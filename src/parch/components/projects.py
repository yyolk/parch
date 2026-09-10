"""Projects board, ticket index, and per-ticket three-card pages — data only."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectsBoard:
    """G three-card well. Ticket dests set ``index_dest`` and ``number`` (header chip)."""

    year: int
    cards: int
    tasks: int
    index_dest: str = ""
    number: int = 0


@dataclass(frozen=True, slots=True)
class ProjectTicket:
    """One stacked ticket on the index — stub number + three-card projects dest."""

    number: int
    dest: str


@dataclass(frozen=True, slots=True)
class ProjectsIndex:
    """Thesis L — stacked tickets. Stub and preview cards link; write-in stays unlinkable."""

    year: int
    dest: str
    tickets: tuple[ProjectTicket, ...]
