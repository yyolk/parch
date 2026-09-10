"""Thesis J experiment — projects × criteria scorecard. Data only."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectsMatrix:
    year: int
    rows: int
    criteria: int
