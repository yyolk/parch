"""Engineering computation pad — data only. Duplex: front write-in, back grid."""

from dataclasses import dataclass
from typing import Literal

type EngineeringFace = Literal["front", "back"]


@dataclass(frozen=True, slots=True)
class EngineeringPad:
    """One face of a duplex computation sheet."""

    face: EngineeringFace
    year: int
    sheet: int = 1
    sheets: int = 1
