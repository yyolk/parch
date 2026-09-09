"""Quarter grid — data only. Three mini-months; pressed months carry dests."""

from dataclasses import dataclass

from parch.components.annual import AnnualMonth


@dataclass(frozen=True, slots=True)
class QuarterGrid:
    year: int
    quarter: int
    months: tuple[AnnualMonth, ...]
