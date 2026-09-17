"""Favorites rankings page — data only. Painters seat the two-column well."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FavoritesPage:
    """Year-scoped rankings well. 2×3 cards; icons are painter-sealed."""

    year: int
