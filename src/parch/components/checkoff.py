"""365 Days Check-Off Sheet — data only. Day count comes from the spec year."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Checkoff365:
    year: int
    days: int
    day_dests: tuple[str | None, ...]
