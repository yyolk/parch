"""Computation pad face — data only. Front is header+well; back is the grid."""

from dataclasses import dataclass
from typing import Literal

type PadSide = Literal["front", "back"]


@dataclass(frozen=True, slots=True)
class PadFace:
    year: int
    sheet: int
    sheets: int
    face: PadSide
    grid_pitch_mm: float
    major_every: int
    header: bool
