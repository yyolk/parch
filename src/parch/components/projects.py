"""Projects board — data only. Painters seat the cards."""

from dataclasses import dataclass

# Thesis B — how many compact rows fit a Nomad well while staying writable.
ROSTER_ROWS = 8


@dataclass(frozen=True, slots=True)
class ProjectsBoard:
    year: int
    cards: int
    tasks: int


@dataclass(frozen=True, slots=True)
class ProjectsRoster:
    """Thesis B — dense overview. Painters seat compact rows; no task/notes knobs."""

    year: int
    rows: int
