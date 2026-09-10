"""Projects board, ticket index, and one-project leaf — data only."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectsBoard:
    year: int
    cards: int
    tasks: int


@dataclass(frozen=True, slots=True)
class ProjectTicket:
    """One stacked ticket on the index — printed title + leaf dest."""

    number: int
    title: str
    dest: str


@dataclass(frozen=True, slots=True)
class ProjectsIndex:
    """Thesis L — stacked tickets. Each row is a whole-ticket link."""

    year: int
    dest: str
    tickets: tuple[ProjectTicket, ...]


@dataclass(frozen=True, slots=True)
class ProjectPage:
    """One G-craft card. ``index_dest`` is the Index chip back-link."""

    year: int
    number: int
    title: str
    dest: str
    index_dest: str
    tasks: int
