"""Projects index — data only. Painters seat the titled mini-cover grid."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectsIndex:
    year: int
    dests: tuple[str, ...]
    titles: tuple[str, ...]
