"""Tiny press spec — TOML or defaults."""

from __future__ import annotations

import calendar
import tomllib
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from parch import ConfigError

_WEEK_STARTS = {"monday": 0, "sunday": 6}


@dataclass(frozen=True)
class Spec:
    year: int = 2026
    device: str = "supernote-nomad"
    week_start: str = "monday"
    month: int = 1
    day: int = 5
    title: str = "Year planner"
    schedule_from: int = 7
    schedule_to: int = 16
    notes_pages: int = 2

    def __post_init__(self) -> None:
        if self.week_start not in _WEEK_STARTS:
            raise ConfigError(f"week_start must be monday or sunday, not {self.week_start!r}")
        if not 1 <= self.month <= 12:
            raise ConfigError(f"month out of range: {self.month}")
        last = calendar.monthrange(self.year, self.month)[1]
        if not 1 <= self.day <= last:
            raise ConfigError(f"day {self.day} is not in {self.year}-{self.month:02d}")
        if not 0 <= self.schedule_from <= self.schedule_to <= 23:
            raise ConfigError("schedule hours must be 0–23 and from ≤ to")
        if self.notes_pages < 0:
            raise ConfigError("notes_pages must be >= 0")

    @property
    def weekday_start(self) -> int:
        return _WEEK_STARTS[self.week_start]

    @property
    def date(self) -> date:
        return date(self.year, self.month, self.day)

    @property
    def cover_dest(self) -> str:
        return "cover"

    @property
    def month_dest(self) -> str:
        return f"month-{self.year:04d}-{self.month:02d}"

    @property
    def day_dest(self) -> str:
        return self.date.isoformat()

    def notes_dest(self, index: int) -> str:
        """1-based notes well dest, e.g. ``2026-01-05-notes-1``."""
        if index < 1:
            raise ConfigError(f"notes dest index must be >= 1, not {index}")
        return f"{self.day_dest}-notes-{index}"

    @classmethod
    def from_mapping(cls, data: dict) -> Spec:
        daily = data.get("daily") or {}
        daily_notes = data.get("daily_notes") or {}
        notes_pages = daily.get(
            "notes_pages",
            data.get("notes_pages", daily_notes.get("pages", 2)),
        )
        return cls(
            year=int(data.get("year", 2026)),
            device=str(data.get("device", "supernote-nomad")),
            week_start=str(data.get("week_start", "monday")).lower(),
            month=int(data.get("month", 1)),
            day=int(data.get("day", 5)),
            title=str(data.get("title", "Year planner")),
            schedule_from=int(daily.get("schedule_from", data.get("schedule_from", 7))),
            schedule_to=int(daily.get("schedule_to", data.get("schedule_to", 16))),
            notes_pages=int(notes_pages),
        )

    @classmethod
    def from_path(cls, path: Path) -> Spec:
        raw = path.read_text(encoding="utf-8")
        try:
            data = tomllib.loads(raw)
        except tomllib.TOMLDecodeError as exc:
            raise ConfigError(f"invalid TOML {path}: {exc}") from exc
        if not isinstance(data, dict):
            raise ConfigError(f"{path} must be a TOML table")
        return cls.from_mapping(data)
