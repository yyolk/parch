"""Engineering / computation pad — data only. Face selects front vs verso ink."""

from dataclasses import dataclass
from typing import Literal

type PadFace = Literal["front", "back"]


@dataclass(frozen=True, slots=True)
class EngineeringPad:
    """One component for both faces. The painter branches on ``face``."""

    face: PadFace
    year: int
    title: str
    other_dest: str
