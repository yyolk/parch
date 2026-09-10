"""Projects board, named timeline index, and leaves — data only."""

from dataclasses import dataclass


# Chronological catalog. Default index uses the first 7; 8 includes the last.
PROJECT_TIMELINE: tuple[tuple[str, str], ...] = (
    ("New desk", "Feb"),
    ("Cabin reno", "Mar"),
    ("Garden beds", "Apr"),
    ("Summer trip", "Jun"),
    ("Studio move", "Aug"),
    ("Book draft", "Sep"),
    ("Year review", "Dec"),
    ("Family reunion", "Oct"),
)


def timeline_nodes(n: int) -> tuple[tuple[str, str], ...]:
    """Printed (name, when) pairs, chronological. ``n`` is 6–8."""
    catalog = PROJECT_TIMELINE
    if n <= 7:
        return catalog[:n]
    return (
        catalog[0],
        catalog[1],
        catalog[2],
        catalog[3],
        catalog[4],
        catalog[5],
        catalog[7],
        catalog[6],
    )


@dataclass(frozen=True, slots=True)
class ProjectsBoard:
    year: int
    cards: int
    tasks: int


@dataclass(frozen=True, slots=True)
class ProjectNode:
    """One named milestone on the index spine."""

    name: str
    when: str
    dest: str


@dataclass(frozen=True, slots=True)
class ProjectsIndex:
    """Named timeline — printed titles beside spine nodes, each a leaf dest."""

    year: int
    nodes: tuple[ProjectNode, ...]


@dataclass(frozen=True, slots=True)
class ProjectLeaf:
    """One project page linked from the timeline."""

    year: int
    number: int
    name: str
    when: str
    tasks: int
    index_dest: str
