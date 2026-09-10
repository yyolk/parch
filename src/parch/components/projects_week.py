"""Thesis K experiment — this week’s two project cards. Data only."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectsWeek:
    year: int
    cards: int
    tasks: int
