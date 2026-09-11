"""Cover title — data only."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CoverTitle:
    year: int
    subtitle: str
    device_name: str
    cta_label: str
    cta_dest: str
