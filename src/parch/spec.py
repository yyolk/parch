"""Tiny press spec — TOML or defaults."""

import calendar
import tomllib
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from string.templatelib import Interpolation, Template

from parch import ConfigError
from parch.calendar import quarter_of

_WEEK_STARTS = {"monday": 0, "sunday": 6}

type TomlTable = dict[str, object]


def _habit_columns(data: TomlTable, habits_table: TomlTable) -> int:
    """Sealed default is 10 columns. Prefer ``[habits] columns``; ``rows`` still accepted."""
    for table, key in (
        (habits_table, "columns"),
        (habits_table, "rows"),
        (data, "habit_columns"),
        (data, "habit_rows"),
    ):
        if key in table:
            return int(table[key])
    return 10


def _parse_months(data: TomlTable) -> tuple[int, ...]:
    raw = data.get("months")
    if isinstance(raw, list) and raw:
        return tuple(int(month) for month in raw)
    if "month" in data:
        return (int(data["month"]),)
    return tuple(range(1, 13))


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
    months: tuple[int, ...] = tuple(range(1, 13))
    # Unused by nav. TOML/CLI leftover — not a generation-time “today”.
    day: int = 5
    title: str = "Year planner"
    schedule_from: int = 7
    schedule_to: int = 16
    notes_pages: int = 2
    habit_columns: int = 10
    priority_rows: int = 6
    project_cards: int = 3
    project_tasks: int = 4
    project_waiting_rows: int = 3

    def __post_init__(self) -> None:
        if self.week_start not in _WEEK_STARTS:
            raise ConfigError(f"week_start must be monday or sunday, not {self.week_start!r}")
        if not self.months:
            raise ConfigError("months must not be empty")
        seen: set[int] = set()
        for month in self.months:
            if not 1 <= month <= 12:
                raise ConfigError(f"month out of range: {month}")
            if month in seen:
                raise ConfigError(f"duplicate month {month}")
            seen.add(month)
        last = calendar.monthrange(self.year, self.month)[1]
        if not 1 <= self.day <= last:
            raise ConfigError(f"day {self.day} is not in {self.year}-{self.month:02d}")
        if not 0 <= self.schedule_from <= self.schedule_to <= 23:
            raise ConfigError("schedule hours must be 0–23 and from ≤ to")
        if self.notes_pages < 0:
            raise ConfigError("notes_pages must be >= 0")
        if not 4 <= self.habit_columns <= 16:
            raise ConfigError("habit_columns must be 4–16")
        if not 4 <= self.priority_rows <= 8:
            raise ConfigError("priority_rows must be 4–8")
        if not 2 <= self.project_cards <= 4:
            raise ConfigError("project_cards must be 2–4")
        if not 3 <= self.project_tasks <= 6:
            raise ConfigError("project_tasks must be 3–6")
        if not 2 <= self.project_waiting_rows <= 3:
            raise ConfigError("project_waiting_rows must be 2–3")

    @property
    def weekday_start(self) -> int:
        return _WEEK_STARTS[self.week_start]

    @property
    def month(self) -> int:
        """First pressed month — MON landing for year/cover."""
        return self.months[0]

    def presses(self, month: int) -> bool:
        return month in self.months

    def presses_day(self, day: date) -> bool:
        """True when ``day`` is in this spec’s year and a pressed month."""
        return day.year == self.year and self.presses(day.month)

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

    def dest_for_habits(self, month: int) -> str:
        return _dest(t"month-{self.year:04d}-{month:02d}-habits")

    @property
    def projects_dest(self) -> str:
        return _dest(t"projects-{self.year:04d}")

    @property
    def projects_waiting_dest(self) -> str:
        return _dest(t"projects-waiting-{self.year:04d}")

    def dest_for_quarter(self, quarter: int) -> str:
        if not 1 <= quarter <= 4:
            raise ConfigError(f"quarter out of range: {quarter}")
        return _dest(t"quarter-{self.year:04d}-Q{quarter}")

    def dest_for_quarter_of(self, month: int) -> str:
        return self.dest_for_quarter(quarter_of(month))

    @property
    def quarter_dest(self) -> str:
        return self.dest_for_quarter_of(self.month)

    def pressed_quarters(self) -> tuple[int, ...]:
        seen: list[int] = []
        for month in self.months:
            quarter = quarter_of(month)
            if quarter not in seen:
                seen.append(quarter)
        return tuple(seen)

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
        habits = data.get("habits")
        habits_table = habits if isinstance(habits, dict) else {}
        projects = data.get("projects")
        projects_table = projects if isinstance(projects, dict) else {}
        return cls(
            year=int(data.get("year", 2026)),
            device=str(data.get("device", "supernote-nomad")),
            week_start=str(data.get("week_start", "monday")).lower(),
            months=_parse_months(data),
            day=int(data.get("day", 5)),
            title=str(data.get("title", "Year planner")),
            schedule_from=int(daily_table.get("schedule_from", data.get("schedule_from", 7))),
            schedule_to=int(daily_table.get("schedule_to", data.get("schedule_to", 16))),
            notes_pages=int(notes_pages),
            habit_columns=_habit_columns(data, habits_table),
            priority_rows=int(daily_table.get("priority_rows", data.get("priority_rows", 6))),
            project_cards=int(projects_table.get("cards", data.get("project_cards", 3))),
            project_tasks=int(projects_table.get("tasks", data.get("project_tasks", 4))),
            project_waiting_rows=int(
                projects_table.get("waiting_rows", data.get("project_waiting_rows", 3))
            ),
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
