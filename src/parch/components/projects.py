"""Projects board, write-in chip index, and one-project page — data only."""

from dataclasses import dataclass

# Status glyphs only — names are write-in, not printed.
SAMPLE_STATUSES: tuple[str, ...] = (
    "todo",
    "doing",
    "todo",
    "done",
    "todo",
    "doing",
    "todo",
    "done",
    "todo",
    "doing",
)


@dataclass(frozen=True, slots=True)
class ProjectsBoard:
    year: int
    cards: int
    tasks: int


@dataclass(frozen=True, slots=True)
class ProjectChip:
    """One write-in index pill. ``status`` is a tiny glyph; name is blank."""

    dest: str
    status: str


@dataclass(frozen=True, slots=True)
class ProjectsIndex:
    """Thesis F — vertical stack of write-in chips. Each chip links to a leaf."""

    year: int
    dest: str
    chips: tuple[ProjectChip, ...]


@dataclass(frozen=True, slots=True)
class ProjectPage:
    """One G-craft card. ``index_dest`` is the Index chip back-link."""

    year: int
    slot: int
    dest: str
    index_dest: str
    tasks: int
    status: str
