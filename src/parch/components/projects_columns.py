"""Thesis A column board — data only. Painters seat the columns."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectsColumns:
    year: int
    cards: int
    ticks: int
