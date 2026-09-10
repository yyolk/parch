"""Projects board and checklist index — data only. Painters seat the cards."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectsBoard:
    year: int
    cards: int
    tasks: int


@dataclass(frozen=True, slots=True)
class ProjectIndexItem:
    """One named checklist row: printed name + dest/page number."""

    name: str
    dest: str
    page: str


@dataclass(frozen=True, slots=True)
class ProjectsIndexChecklist:
    """Named checklist index — names are printed, not write-in rules."""

    year: int
    items: tuple[ProjectIndexItem, ...]


@dataclass(frozen=True, slots=True)
class ProjectLeaf:
    """One project page linked from the checklist name."""

    year: int
    name: str
    dest: str
    index_dest: str
    page: str
    tasks: int
