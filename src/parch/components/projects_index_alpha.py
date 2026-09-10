"""Thesis C experiment — A–Z projects index and one-project leaves. Data only."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectIndexEntry:
    name: str
    letter: str
    dest: str
    hint: str


@dataclass(frozen=True, slots=True)
class ProjectsIndexAlpha:
    year: int
    index_dest: str
    entries: tuple[ProjectIndexEntry, ...]


@dataclass(frozen=True, slots=True)
class ProjectLeaf:
    year: int
    name: str
    dest: str
    index_dest: str
    hint: str
    tasks: int
