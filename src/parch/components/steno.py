"""Gregg stenographer pad — data only. Single face: lined + center rule."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StenoPad:
    """One single-sided sheet. Painter seats ⅓″ Gregg ruling; this holds sheet index."""

    sheet: int
    sheets: int
