"""Projects index — data only. Painters seat the mini-card grid."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectsIndex:
    year: int
    dests: tuple[str, ...]
