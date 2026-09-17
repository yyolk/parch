"""Projects board, ticket index, and per-ticket dest pages — data only."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectsBoard:
    """``paint_project`` well. Ticket dests set ``index_dest`` and ``number`` (header chip)."""

    year: int
    cards: int
    index_dest: str = ""
    number: int = 0


@dataclass(frozen=True, slots=True)
class ProjectTicket:
    """One stacked ticket on the index — stub number + stacked-card projects dest."""

    number: int
    dest: str


@dataclass(frozen=True, slots=True)
class ProjectsIndex:
    """Stacked tickets for ``paint_projects_index``. Stub and preview cards link; write-in stays unlinkable.

    ``cards`` is the dest stack count and the index preview-square count.
    """

    year: int
    dest: str
    tickets: tuple[ProjectTicket, ...]
    cards: int
