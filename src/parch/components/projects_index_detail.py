"""Thesis F experiment — index + one active-project well. Data only."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectsIndexDetail:
    year: int
    index_rows: int
    tasks: int
