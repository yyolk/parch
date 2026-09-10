"""Thesis L experiment — meeting / agenda project capture. Data only."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectsMeeting:
    year: int
    cards: int
    tasks: int
