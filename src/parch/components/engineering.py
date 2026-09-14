"""Engineering computation pad — data only. Front is header + blank well; back is the grid."""

from dataclasses import dataclass
from typing import Literal

type EngineeringFace = Literal["front", "back"]


@dataclass(frozen=True, slots=True)
class EngineeringPad:
    """One face of a duplex sheet. Painters seat header vs 5×5 grid; this holds sheet index."""

    face: EngineeringFace
    sheet: int
    sheets: int
