"""Hourly schedule strip — data only."""

from dataclasses import dataclass
from datetime import time

from tomlrange import Bound


@dataclass(frozen=True, slots=True)
class Schedule:
    label: str
    hours: tuple[int, ...]
    work_hours: Bound[time] | None = None  # Clock Bound; painter intersects per band
