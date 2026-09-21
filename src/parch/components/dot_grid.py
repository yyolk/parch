"""Edge-to-edge dot-grid pad — data only. Single face: clone dots on the full page."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DotGridPad:
    """One single-sided sheet. Painter seats ``paint_dot_grid`` on the device page."""

    sheet: int
    sheets: int
