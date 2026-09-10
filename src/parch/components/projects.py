"""Projects index and leaves — data only. Painters seat the TOC and G cards."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectEntry:
    """One TOC row: write-in name well, leaf dest, dest number."""

    dest: str
    number: str


@dataclass(frozen=True, slots=True)
class ProjectsIndex:
    year: int
    entries: tuple[ProjectEntry, ...]


@dataclass(frozen=True, slots=True)
class ProjectLeaf:
    year: int
    dest: str
    number: str
    tasks: int
