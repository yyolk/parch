"""Edge-to-edge perspective grid — data only. Single face: full-bleed mesh."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PerspectivePad:
    """One single-sided sheet. Painter seats the grid on the page rect."""

    sheet: int
    sheets: int
