"""Gregg stenographer pad — data only. Ruling is fitted in the painter."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GreggPad:
    """One single-sided Gregg page. Painters snap ⅓″ ruling to content_frame."""

    page: int
