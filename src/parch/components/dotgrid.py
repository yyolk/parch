"""Full-bleed e-ink dot grid — data only. Single face, no chrome."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DotGridPad:
    """One single-sided sheet. Painter seats clone-dot pitch on the page bounds."""

    sheet: int
    sheets: int
