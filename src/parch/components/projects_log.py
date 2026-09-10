"""Thesis N experiment — one-project dated progress journal. Data only."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectsLog:
    year: int
    entries: int
