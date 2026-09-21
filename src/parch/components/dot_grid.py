"""Edge-to-edge clone-pitch dot grid — data only. Painter bleeds the page."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DotGrid:
    """One single-sided sheet. Painter fills page bleed at ``CLONE_DOT_*``."""

    sheet: int
    sheets: int
