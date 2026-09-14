"""Gregg stenographer pad — data only. Ruling geometry lives in layout seats."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StenoPad:
    """One single-sided Gregg face. Painters ink seats; this holds sheet index."""

    sheet: int
    sheets: int
