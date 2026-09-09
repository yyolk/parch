"""Lined notes well — data only."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Notes:
    label: str
