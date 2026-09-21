"""Blank full-bleed clone-dot page — data only. Painters skip planner chrome."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DotGridPage:
    """One extra year-planner writing sheet. ``page`` is 1-based."""

    page: int
    pages: int
