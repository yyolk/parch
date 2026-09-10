"""Projects board and index — data only. Painters seat the cards and roster."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectsBoard:
    year: int
    cards: int
    tasks: int


@dataclass(frozen=True, slots=True)
class ProjectsIndex:
    """Dense linked roster — one dest per row."""

    year: int
    dests: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProjectLeaf:
    """One project page linked from the index."""

    year: int
    number: int
    tasks: int
    index_dest: str
