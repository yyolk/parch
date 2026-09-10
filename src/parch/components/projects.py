"""Projects directory and leaf — data only. Painters seat the names."""

from dataclasses import dataclass

SAMPLE_TITLES = (
    "North Cabin",
    "Atlas Notes",
    "River Path",
    "Harbor Desk",
    "Cedar Shelf",
    "Night Train",
    "Paper Mill",
    "Quiet Field",
    "Iron Bridge",
    "Glass House",
    "Winter Desk",
    "Open Studio",
    "Field Archive",
    "Copper Roof",
    "Sunday Press",
    "Maple Annex",
)


@dataclass(frozen=True, slots=True)
class ProjectsBoard:
    year: int
    cards: int
    tasks: int


@dataclass(frozen=True, slots=True)
class ProjectsIndex:
    """Thesis J — two-column named directory. Each name has a leaf dest."""

    year: int
    names: tuple[str, ...]
    dests: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProjectLeaf:
    """One G-craft project page linked from the directory."""

    year: int
    number: int
    name: str
    tasks: int
    dest: str
    index_dest: str


def sample_titles(count: int) -> tuple[str, ...]:
    """First ``count`` printed sample titles. Repeats the list if needed."""
    if count < 1:
        raise ValueError(f"count must be >= 1, not {count}")
    titles = SAMPLE_TITLES
    return tuple(titles[i % len(titles)] for i in range(count))
