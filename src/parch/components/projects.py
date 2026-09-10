"""Projects board, timeline index, and leaves — data only."""

from dataclasses import dataclass


# Chronological month marks. Default index uses the first 7; 8 inserts Oct.
PROJECT_TIMELINE_MONTHS: tuple[str, ...] = (
    "Feb",
    "Mar",
    "Apr",
    "Jun",
    "Aug",
    "Sep",
    "Dec",
    "Oct",
)


def timeline_months(n: int) -> tuple[str, ...]:
    """Printed month marks, chronological. ``n`` is 6–8."""
    catalog = PROJECT_TIMELINE_MONTHS
    if n <= 7:
        return catalog[:n]
    return (*catalog[:6], catalog[7], catalog[6])


@dataclass(frozen=True, slots=True)
class ProjectsBoard:
    year: int
    cards: int
    tasks: int


@dataclass(frozen=True, slots=True)
class ProjectNode:
    """One write-in milestone on the index spine."""

    when: str
    dest: str


@dataclass(frozen=True, slots=True)
class ProjectsIndex:
    """Timeline — write-in name rules beside spine nodes, each a leaf dest."""

    year: int
    nodes: tuple[ProjectNode, ...]


@dataclass(frozen=True, slots=True)
class ProjectLeaf:
    """One project page linked from the timeline."""

    year: int
    number: int
    tasks: int
    index_dest: str
