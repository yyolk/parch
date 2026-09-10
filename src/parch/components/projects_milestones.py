"""Thesis O experiment — one-project milestone ladder. Data only."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectsMilestones:
    year: int
    rungs: int
