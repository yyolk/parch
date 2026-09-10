"""Thesis D experiment — status-banded projects index. Data only."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectIndexRow:
    dest: str


@dataclass(frozen=True, slots=True)
class ProjectIndexBand:
    label: str
    rows: tuple[ProjectIndexRow, ...]


@dataclass(frozen=True, slots=True)
class ProjectsIndexBands:
    year: int
    bands: tuple[ProjectIndexBand, ...]


@dataclass(frozen=True, slots=True)
class ProjectLeaf:
    """One G-craft project page. Back-link dest lives here; painters do not invent it."""

    year: int
    tasks: int
    index_dest: str
