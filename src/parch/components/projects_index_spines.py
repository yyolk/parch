"""Thesis N experiment — shelf of named project spines and one-project leaves. Data only."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectSpine:
    name: str
    dest: str
    hint: str


@dataclass(frozen=True, slots=True)
class ProjectsIndexSpines:
    year: int
    index_dest: str
    spines: tuple[ProjectSpine, ...]


@dataclass(frozen=True, slots=True)
class ProjectLeaf:
    year: int
    name: str
    dest: str
    index_dest: str
    hint: str
    tasks: int
