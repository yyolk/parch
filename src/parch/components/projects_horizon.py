"""Thesis I experiment — time-horizon project strip. Data only."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectsHorizon:
    year: int
    slots: int
    ticks: int
