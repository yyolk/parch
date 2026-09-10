"""One project sheet — data only. Painters reuse the G card craft."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectSheet:
    year: int
    number: int
    title: str
    tasks: int
    index_dest: str
