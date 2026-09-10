"""Projects index and leaf — data only. Painters seat the table and G craft."""

from dataclasses import dataclass

# Status samples only — names are write-in underlines on the index and leaf.
SAMPLE_STATUSES: tuple[str, ...] = (
    "Doing",
    "Todo",
    "Done",
    "Doing",
    "Todo",
    "Doing",
    "Done",
    "Todo",
    "Doing",
    "Todo",
    "Doing",
    "Todo",
)


def sample_statuses(n: int) -> tuple[str, ...]:
    """First ``n`` status labels for index rows / leaves."""
    return SAMPLE_STATUSES[:n]


@dataclass(frozen=True, slots=True)
class ProjectsBoard:
    year: int
    cards: int
    tasks: int


@dataclass(frozen=True, slots=True)
class ProjectEntry:
    status: str
    dest: str


@dataclass(frozen=True, slots=True)
class ProjectsIndex:
    """Thesis G — write-in name / status table. Each row is a dest."""

    year: int
    entries: tuple[ProjectEntry, ...]


@dataclass(frozen=True, slots=True)
class ProjectLeaf:
    """One project page linked from the index. G clone+fit craft."""

    year: int
    number: int
    status: str
    tasks: int
    index_dest: str
