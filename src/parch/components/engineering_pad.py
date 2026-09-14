"""Engineering pad front/back — data only. Painters ink header vs grid."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EngineeringPadFront:
    """Duplex front — Title/No., Name/Date, Subject/Sheet header + blank well."""

    year: int
    sheet: int
    sheets: int


@dataclass(frozen=True, slots=True)
class EngineeringPadBack:
    """Duplex back — 5×5 major/minor engineering grid. No header."""

    year: int
    sheet: int
    sheets: int
