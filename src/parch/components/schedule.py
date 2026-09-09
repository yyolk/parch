"""Hourly schedule strip — data only."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Schedule:
    label: str
    hours: tuple[int, ...]
