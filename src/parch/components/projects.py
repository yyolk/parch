"""Projects board and one-project detail — data only. Painters seat them."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectsBoard:
    year: int
    cards: int
    tasks: int


@dataclass(frozen=True, slots=True)
class ProjectDetail:
    """Thesis C — one project filling the Nomad well. Sample page only."""

    year: int
    tasks: int
