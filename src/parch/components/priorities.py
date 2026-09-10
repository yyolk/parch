"""Daily priorities checklist — data only. Painters draw ticks."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Priorities:
    label: str
    rows: int
