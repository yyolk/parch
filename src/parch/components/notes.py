"""Lined notes well — data only. Used on the daily seat and on daily_notes pages."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Notes:
    label: str
