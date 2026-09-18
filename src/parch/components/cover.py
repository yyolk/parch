"""Cover title — data only."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CoverTitle:
    year: int
    cta_label: str
    cta_dest: str
    eyebrow: str = "Year Book"
    specs_lead: str = "monday weeks"
    display_title: str | None = None
