"""Gregg / stenographer pad — data only. Painters ink the ruling from these knobs."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StenoPad:
    """One single-sided sheet. Pitch and center_rule change pixels; no header copy."""

    line_pitch_mm: float
    center_rule: bool
    sheet: int
    sheets: int
