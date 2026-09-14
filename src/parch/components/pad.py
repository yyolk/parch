"""Engineering / computation pad wells — data only. Pairing lives on PadSheet."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PadBlank:
    """Front well: header + empty writing area. No grid, no holes."""

    number: int
    of: int
    year: int


@dataclass(frozen=True, slots=True)
class PadGrid:
    """Back well: 5×5 major/minor square grid. No header, no holes."""

    number: int
    of: int
    year: int
    major: int = 5
