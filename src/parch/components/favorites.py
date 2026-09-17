"""Favorites rankings page — data only. Painters seat the two-column well."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FavoritesPage:
    """Year-scoped Hobonichi-style rankings well. Caption and icons are painter-sealed."""

    year: int
