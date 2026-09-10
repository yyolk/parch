"""Projects directory and leaf — data only. Painters seat the underlines."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectsBoard:
    year: int
    cards: int
    tasks: int


@dataclass(frozen=True, slots=True)
class ProjectsIndex:
    """Thesis J — two-column write-in directory. Each row links to a leaf."""

    year: int
    dests: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProjectLeaf:
    """One G-craft project page linked from the directory."""

    year: int
    number: int
    tasks: int
    dest: str
    index_dest: str
