"""Gregg stenographer pad — data only. Single face: lined + center rule."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StenoPad:
    """One single-sided sheet. Painter seats 5 mm ruling; this holds sheet index."""

    sheet: int
    sheets: int
