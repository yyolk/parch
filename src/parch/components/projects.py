"""Projects board, named-chip index, and one-project page — data only."""

from dataclasses import dataclass

# Printed sample titles — index chips, not write-in underlines.
SAMPLE_PROJECTS: tuple[tuple[str, str], ...] = (
    ("Kitchen reno", "todo"),
    ("Parch MVP", "doing"),
    ("Taxes 2026", "todo"),
    ("Garden beds", "done"),
    ("Cabin trip", "todo"),
    ("Piano lessons", "doing"),
    ("Visa renewal", "todo"),
    ("Bike overhaul", "done"),
    ("Studio move", "todo"),
    ("Roof patch", "doing"),
)


@dataclass(frozen=True, slots=True)
class ProjectsBoard:
    year: int
    cards: int
    tasks: int


@dataclass(frozen=True, slots=True)
class ProjectChip:
    """One named index pill. ``status`` is a tiny glyph, not a write-in."""

    title: str
    dest: str
    status: str


@dataclass(frozen=True, slots=True)
class ProjectsIndex:
    """Thesis F — vertical stack of named chips. Each chip links to a leaf."""

    year: int
    dest: str
    chips: tuple[ProjectChip, ...]


@dataclass(frozen=True, slots=True)
class ProjectPage:
    """One G-craft card. ``index_dest`` is the Index chip back-link."""

    year: int
    slot: int
    title: str
    dest: str
    index_dest: str
    tasks: int
    status: str
