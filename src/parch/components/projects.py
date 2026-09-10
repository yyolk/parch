"""Projects index and leaf — data only. Painters seat the table and G craft."""

from dataclasses import dataclass

# Printed sample titles for the exploratory index. Not write-in underlines.
SAMPLE_PROJECTS: tuple[tuple[str, str], ...] = (
    ("Kitchen renovation", "Doing"),
    ("JLPT N3 study", "Todo"),
    ("Cabin trip kit", "Done"),
    ("Raised garden beds", "Doing"),
    ("Photo archive", "Todo"),
    ("Bike overhaul", "Doing"),
    ("Family cookbook", "Done"),
    ("Studio desk build", "Todo"),
    ("Reading stack", "Doing"),
    ("Guest room refresh", "Todo"),
    ("Sourdough starter", "Doing"),
    ("Attic sort", "Todo"),
)


def sample_projects(n: int) -> tuple[tuple[str, str], ...]:
    """First ``n`` printed (name, status) pairs from the sample catalog."""
    return SAMPLE_PROJECTS[:n]


@dataclass(frozen=True, slots=True)
class ProjectsBoard:
    year: int
    cards: int
    tasks: int


@dataclass(frozen=True, slots=True)
class ProjectEntry:
    name: str
    status: str
    dest: str


@dataclass(frozen=True, slots=True)
class ProjectsIndex:
    """Thesis G — printed name / status table. Each row is a dest."""

    year: int
    entries: tuple[ProjectEntry, ...]


@dataclass(frozen=True, slots=True)
class ProjectLeaf:
    """One named project page linked from the index. G clone+fit craft."""

    year: int
    number: int
    name: str
    status: str
    tasks: int
    index_dest: str
