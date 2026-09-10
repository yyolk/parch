"""Projects board and checklist index — data only. Painters seat the cards."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectsBoard:
    year: int
    cards: int
    tasks: int


@dataclass(frozen=True, slots=True)
class ProjectIndexItem:
    """One checklist row: write-in name rule + dest/page number."""

    dest: str
    page: str


@dataclass(frozen=True, slots=True)
class ProjectsIndexChecklist:
    """Write-in checklist index — empty name underlines, dest/page numbers."""

    year: int
    items: tuple[ProjectIndexItem, ...]


@dataclass(frozen=True, slots=True)
class ProjectLeaf:
    """One project page linked from the checklist name rule."""

    year: int
    dest: str
    index_dest: str
    page: str
    tasks: int
