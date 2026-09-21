"""Edge-to-edge clone-dot sheet — data only. Full-bleed page; no chrome."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DotGridSheet:
    """One coverless sheet. Painter fills the physical page; this holds sheet index."""

    sheet: int
    sheets: int
