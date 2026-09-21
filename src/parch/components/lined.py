"""Edge-to-edge lined page — data only. Single face: full-bleed rules."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LinedPad:
    """One single-sided sheet. Painter seats LINE_PITCH on the page rect."""

    sheet: int
    sheets: int
