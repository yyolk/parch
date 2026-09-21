"""Edge-to-edge clone-dot page — data only. Single face: full-bleed dots."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DotGridPad:
    """One single-sided sheet. Painter seats CLONE_DOT_* on the page rect."""

    sheet: int
    sheets: int
