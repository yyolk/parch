"""Full-bleed clone-pitch dot-grid pad — data only. No header or ruling extras."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DotGridPad:
    """One single-sided sheet. Painter fills ``Device.page_rect`` at clone pitch."""

    sheet: int
    sheets: int
