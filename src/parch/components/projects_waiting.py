"""Thesis P experiment — Moving / Waiting / Blocked friction board. Data only."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectsWaiting:
    year: int
    rows: int
