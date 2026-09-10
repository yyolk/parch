"""Projects board and index — data only. Painters seat the cards and roster."""

from collections.abc import Callable
from dataclasses import dataclass

# G strip, left → right. Tenth row reuses triangle.
PROJECT_GLYPHS = (
    "triangle",
    "cross",
    "hexagon",
    "square",
    "crescent",
    "diamond",
    "circle",
    "plus",
    "star",
)

# Catalog labels (not inked — index name fields are write-in underlines).
PROJECT_ROSTER = (
    ("Cabin reno", "Doing"),
    ("Thesis draft", "Todo"),
    ("Garden beds", ""),
    ("Studio move", "Doing"),
    ("Night course", "Todo"),
    ("Family trip", ""),
    ("Health plan", "Doing"),
    ("Side studio", "Todo"),
    ("Year theme", "Done"),
    ("Attic store", "Todo"),
)


@dataclass(frozen=True, slots=True)
class ProjectsBoard:
    year: int
    cards: int
    tasks: int


@dataclass(frozen=True, slots=True)
class ProjectEntry:
    """One index row — glyph + write-in name dest + optional status."""

    title: str
    glyph: str
    status: str
    dest: str


@dataclass(frozen=True, slots=True)
class ProjectsIndex:
    """Glyph + write-in roster — each name underline dests to a leaf."""

    year: int
    rows: tuple[ProjectEntry, ...]


@dataclass(frozen=True, slots=True)
class ProjectLeaf:
    """G-craft project page linked from the index."""

    year: int
    number: int
    title: str
    glyph: str
    status: str
    tasks: int
    index_dest: str


def project_roster(n: int, dest_for: Callable[[int], str]) -> tuple[ProjectEntry, ...]:
    """First ``n`` catalog rows, dests from ``dest_for(1-based)``."""
    if n < 1:
        raise ValueError(f"project roster n must be >= 1, not {n}")
    if n > len(PROJECT_ROSTER):
        raise ValueError(f"project roster n {n} exceeds catalog {len(PROJECT_ROSTER)}")
    rows: list[ProjectEntry] = []
    glyphs = PROJECT_GLYPHS
    for i, (title, status) in enumerate(PROJECT_ROSTER[:n]):
        rows.append(
            ProjectEntry(
                title=title,
                glyph=glyphs[i % len(glyphs)],
                status=status,
                dest=dest_for(i + 1),
            )
        )
    return tuple(rows)
