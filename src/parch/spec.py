"""Tiny press spec — TOML or defaults."""

import calendar
import tomllib
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from string.templatelib import Interpolation, Template

from parch import ConfigError

_WEEK_STARTS = {"monday": 0, "sunday": 6}

type TomlTable = dict[str, object]


def _dest(template: Template) -> str:
    """Flatten a dest t-string (prefix + fields + format specs)."""
    chunks: list[str] = []
    for part in template:
        match part:
            case Interpolation(value=value, format_spec=spec) if spec:
                chunks.append(format(value, spec))
            case Interpolation(value=value):
                chunks.append(str(value))
            case str() as literal:
                chunks.append(literal)
    return "".join(chunks)


@dataclass(frozen=True, slots=True)
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
    def year_dest(self) -> str:
        return _dest(t"year-{self.year:04d}")

    @property
    def month_dest(self) -> str:
        return self.dest_for_month(self.month)

    def dest_for_month(self, month: int) -> str:
        return _dest(t"month-{self.year:04d}-{month:02d}")

    @property
    def day_dest(self) -> str:
        return self.date.isoformat()

    def dest_for_day(self, day: date) -> str:
        return day.isoformat()

    def dest_for_week(self, day: date) -> str:
        """ISO week dest, e.g. ``week-2026-W01``. Monday-start book weeks align with ISO."""
        iso = day.isocalendar()
        return _dest(t"week-{iso.year:04d}-W{iso.week:02d}")

    def dest_for_notes(self, day: date, index: int) -> str:
        """1-based notes well dest, e.g. ``2026-01-05-notes-1``."""
        if index < 1:
            raise ConfigError(f"notes dest index must be >= 1, not {index}")
        return _dest(t"{day.isoformat()}-notes-{index}")

    def notes_dest(self, index: int) -> str:
        return self.dest_for_notes(self.date, index)

    @classmethod
    def from_mapping(cls, data: TomlTable) -> Spec:
        daily = data.get("daily")
        daily_notes = data.get("daily_notes")
        daily_table = daily if isinstance(daily, dict) else {}
        notes_table = daily_notes if isinstance(daily_notes, dict) else {}
        notes_pages = daily_table.get(
            "notes_pages",
            data.get("notes_pages", notes_table.get("pages", 2)),
        )
        return cls(
            year=int(data.get("year", 2026)),
            device=str(data.get("device", "supernote-nomad")),
            week_start=str(data.get("week_start", "monday")).lower(),
            month=int(data.get("month", 1)),
            day=int(data.get("day", 5)),
            title=str(data.get("title", "Year planner")),
            schedule_from=int(daily_table.get("schedule_from", data.get("schedule_from", 7))),
            schedule_to=int(daily_table.get("schedule_to", data.get("schedule_to", 16))),
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
