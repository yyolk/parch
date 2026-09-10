"""Projects board, index, and one-project page — data only. Painters seat them."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectsBoard:
    year: int
    cards: int
    tasks: int


@dataclass(frozen=True, slots=True)
class ProjectsIndex:
    """Thesis E — featured dest + compact linked roster dests."""

    year: int
    dest: str
    featured: str
    entries: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProjectPage:
    """One G-craft card. ``index_dest`` is the PROJ back-link."""

    year: int
    slot: int
    dest: str
    index_dest: str
    tasks: int
