"""Thesis M experiment — parking lot + one active card. Data only."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectsParking:
    year: int
    lot_rows: int
    tasks: int
