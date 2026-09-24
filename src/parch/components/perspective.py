"""Edge-to-edge perspective grid — data only. Single face: full-bleed square grid and rays."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PerspectivePad:
    """One single-sided sheet. Painter seats the grid on the full page rect."""

    sheet: int
    sheets: int
