"""Tiny press spec — TOML or defaults."""

import tomllib
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from string.templatelib import Interpolation, Template

from parch import ConfigError
from parch.calendar import quarter_of
from parch.components.bujo import FUTURE_LOG_MONTHS_PER_PAGE
from parch.fonts.ramp import TypeOverlay, require_overlay

_WEEK_STARTS = {"monday": 0, "sunday": 6}
_BOOKS = frozenset(
    {
        "year-planner",
        "projects-notebook",
        "engineering-notebook",
        "bullet-journal",
    }
)
_BOOK_CHOICES = (
    "year-planner, projects-notebook, engineering-notebook, or bullet-journal"
)
_TYPOGRAPHY_KEYS = frozenset({"overlay"})
_BUJO_KEYS = frozenset({"index_pages", "collections"})

type TomlTable = dict[str, object]


def _parse_typography(data: TomlTable) -> TypeOverlay:
    """``[typography.overlay.<step>]`` → ``TypeOverlay``. Unknown keys fail loudly.

    A present overlay table is validated (exact ``schema_version``, closed
    steps, Jost weights, size bands) before the spec is returned. Missing
    ``[typography]`` is the closed-table default (empty overlay).
    """
    raw = data.get("typography")
    if raw is None:
        return TypeOverlay()
    if not isinstance(raw, dict):
        raise ConfigError("typography must be a TOML table")
    unknown = set(raw) - _TYPOGRAPHY_KEYS
    if unknown:
        key = sorted(unknown)[0]
        raise ConfigError(f"unknown typography key {key!r}")
    overlay = raw.get("overlay")
    if overlay is None:
        return TypeOverlay()
    if not isinstance(overlay, dict):
        raise ConfigError("typography.overlay must be a TOML table")
    return require_overlay(overlay)


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


def _parse_bool(raw: object, key: str) -> bool:
    """Closed boolean TOML field — strings and ints fail loudly."""
    if not isinstance(raw, bool):
        raise ConfigError(f"{key} must be a boolean")
    return raw


def _parse_bujo(data: TomlTable) -> tuple[int, int]:
    """``[bujo]`` index_pages + collections. Unknown keys fail loudly."""
    raw = data.get("bujo")
    if raw is None:
        return 2, 24
    if not isinstance(raw, dict):
        raise ConfigError("bujo must be a TOML table")
    unknown = set(raw) - _BUJO_KEYS
    if unknown:
        key = sorted(unknown)[0]
        raise ConfigError(f"unknown bujo key {key!r}")
    return int(raw.get("index_pages", 2)), int(raw.get("collections", 24))


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
    title: str = "Year planner"
    book: str = "year-planner"
    schedule_from: int = 7
    schedule_to: int = 16
    notes_pages: int = 2
    habit_columns: int = 10
    priority_rows: int = 6
    project_cards: int = 3
    project_tasks: int = 4
    project_tickets: int = 8
    project_index_pages: int = 1
    meeting_index_rows: int = 16
    task_rows: int = 6  # toml floor; dest paint derives the fitted count
    engineering_sheets: int = 0  # duplex fronts+backs; 0 keeps year-planner press
    steno_sheets: int = 0  # single-face Gregg pages; 0 keeps year-planner press
    outline: bool = False  # reader sidebar outline; default off
    bujo_index_pages: int = 2
    bujo_collections: int = 24
    type_overlay: TypeOverlay = field(default_factory=TypeOverlay)

    def __post_init__(self) -> None:
        if self.week_start not in _WEEK_STARTS:
            raise ConfigError(
                f"week_start must be monday or sunday, not {self.week_start!r}"
            )
        if self.book not in _BOOKS:
            raise ConfigError(f"book must be {_BOOK_CHOICES}, not {self.book!r}")
        if self.book == "engineering-notebook" and self.engineering_sheets < 1:
            raise ConfigError("engineering-notebook requires engineering_sheets >= 1")
        if not self.months:
            raise ConfigError("months must not be empty")
        seen: set[int] = set()
        for month in self.months:
            if not 1 <= month <= 12:
                raise ConfigError(f"month out of range: {month}")
            if month in seen:
                raise ConfigError(f"duplicate month {month}")
            seen.add(month)
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
        if not 6 <= self.project_tickets <= 10:
            raise ConfigError("project_tickets must be 6–10")
        if not 1 <= self.project_index_pages <= 6:
            raise ConfigError("project_index_pages must be 1–6")
        if not 12 <= self.meeting_index_rows <= 20:
            raise ConfigError("meeting_index_rows must be 12–20")
        if not 4 <= self.task_rows <= 8:
            raise ConfigError("task_rows must be 4–8")
        if not 0 <= self.engineering_sheets <= 100:
            raise ConfigError("engineering_sheets must be 0–100")
        if not 0 <= self.steno_sheets <= 100:
            raise ConfigError("steno_sheets must be 0–100")
        if self.steno_sheets and self.engineering_sheets:
            raise ConfigError("steno_sheets and engineering_sheets cannot both be set")
        if not 1 <= self.bujo_index_pages <= 6:
            raise ConfigError("bujo index_pages must be 1–6")
        if not 0 <= self.bujo_collections <= 48:
            raise ConfigError("bujo collections must be 0–48")

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
    def project_count(self) -> int:
        """``paint_project`` dest pages: ``index_pages × tickets`` (one row → one projects page)."""
        return self.project_index_pages * self.project_tickets

    def dest_for_projects_index(self, page: int) -> str:
        if not 1 <= page <= self.project_index_pages:
            raise ConfigError(f"projects index page out of range: {page}")
        return _dest(t"projects-index-{self.year:04d}-{page:02d}")

    @property
    def projects_index_dest(self) -> str:
        """Proj landing — index page 1."""
        return self.dest_for_projects_index(1)

    def dest_for_projects_index_of(self, slot: int) -> str:
        """Index page that lists ``slot`` (1-based global row)."""
        if not 1 <= slot <= self.project_count:
            raise ConfigError(f"project slot out of range: {slot}")
        page = (slot - 1) // self.project_tickets + 1
        return self.dest_for_projects_index(page)

    def dest_for_project(self, slot: int) -> str:
        if not 1 <= slot <= self.project_count:
            raise ConfigError(f"project slot out of range: {slot}")
        return _dest(t"projects-{self.year:04d}-{slot:02d}")

    @property
    def meeting_count(self) -> int:
        """Meeting dest pages: one roster row → one ``meeting-{year}-{n:02d}``."""
        return self.meeting_index_rows

    @property
    def meetings_index_dest(self) -> str:
        """Meet landing — dense dated roster."""
        return _dest(t"meetings-index-{self.year:04d}")

    def dest_for_meetings_index_of(self, slot: int) -> str:
        """Index page that lists ``slot`` (single ``paint_meetings_index`` roster)."""
        if not 1 <= slot <= self.meeting_count:
            raise ConfigError(f"meeting slot out of range: {slot}")
        return self.meetings_index_dest

    def dest_for_meeting(self, slot: int) -> str:
        if not 1 <= slot <= self.meeting_count:
            raise ConfigError(f"meeting slot out of range: {slot}")
        return _dest(t"meeting-{self.year:04d}-{slot:02d}")

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

    def dest_for_day(self, day: date) -> str:
        return day.isoformat()

    def dest_for_week(self, day: date) -> str:
        """ISO week dest, e.g. ``week-2026-W01``. Monday-start book weeks align with ISO."""
        iso = day.isocalendar()
        return _dest(t"week-{iso.year:04d}-W{iso.week:02d}")

    def dest_for_tasks_index(self, quarter: int) -> str:
        if not 1 <= quarter <= 4:
            raise ConfigError(f"tasks index quarter out of range: {quarter}")
        return _dest(t"tasks-index-{self.year:04d}-Q{quarter}")

    @property
    def tasks_index_dest(self) -> str:
        """Task landing — first pressed quarter’s month-banded index."""
        return self.dest_for_tasks_index(self.pressed_quarters()[0])

    def dest_for_task(self, day: date) -> str:
        """Weekly Tasks dest, e.g. ``tasks-2026-W01`` — not the planner week page."""
        iso = day.isocalendar()
        return _dest(t"tasks-{iso.year:04d}-W{iso.week:02d}")

    @property
    def review_index_dest(self) -> str:
        """Rev landing — one-page week-grid index for the pressed months."""
        return _dest(t"review-index-{self.year:04d}")

    def dest_for_review(self, day: date) -> str:
        """Weekly Review dest, e.g. ``review-2026-W01`` — not the planner week page."""
        iso = day.isocalendar()
        return _dest(t"review-{iso.year:04d}-W{iso.week:02d}")

    def dest_for_notes(self, day: date, index: int) -> str:
        """1-based notes well dest, e.g. ``2026-01-05-notes-1``."""
        if index < 1:
            raise ConfigError(f"notes dest index must be >= 1, not {index}")
        return _dest(t"{day.isoformat()}-notes-{index}")

    def dest_for_engineering_pad(self, sheet: int, face: str) -> str:
        """1-based duplex dest, e.g. ``engineering-2026-01-front``."""
        if face not in {"front", "back"}:
            raise ConfigError(f"engineering face must be front or back, not {face!r}")
        if self.engineering_sheets < 1:
            raise ConfigError("engineering_sheets must be >= 1 to name a pad dest")
        if not 1 <= sheet <= self.engineering_sheets:
            raise ConfigError(f"engineering sheet out of range: {sheet}")
        return _dest(t"engineering-{self.year:04d}-{sheet:02d}-{face}")

    @property
    def bujo_key_dest(self) -> str:
        return _dest(t"bujo-key-{self.year:04d}")

    def dest_for_bujo_index(self, page: int) -> str:
        if not 1 <= page <= self.bujo_index_pages:
            raise ConfigError(f"bujo index page out of range: {page}")
        return _dest(t"bujo-index-{self.year:04d}-{page:02d}")

    @property
    def bujo_index_dest(self) -> str:
        """Idx landing — index page 1."""
        return self.dest_for_bujo_index(1)

    @property
    def bujo_future_pages(self) -> int:
        """Sealed 3 months/page; at least one future-log page."""
        return max(
            1,
            (len(self.months) + FUTURE_LOG_MONTHS_PER_PAGE - 1)
            // FUTURE_LOG_MONTHS_PER_PAGE,
        )

    def dest_for_bujo_future(self, page: int) -> str:
        if not 1 <= page <= self.bujo_future_pages:
            raise ConfigError(f"bujo future-log page out of range: {page}")
        return _dest(t"bujo-future-{self.year:04d}-{page:02d}")

    @property
    def bujo_future_dest(self) -> str:
        """Fut landing — future-log page 1."""
        return self.dest_for_bujo_future(1)

    def dest_for_month_tasks(self, month: int) -> str:
        return _dest(t"month-{self.year:04d}-{month:02d}-tasks")

    def dest_for_bujo_collection(self, number: int) -> str:
        if not 1 <= number <= self.bujo_collections:
            raise ConfigError(f"bujo collection out of range: {number}")
        return _dest(t"bujo-col-{self.year:04d}-{number:02d}")

    @property
    def bujo_collection_dest(self) -> str:
        """Col landing — collection 01 when collections are pressed."""
        return self.dest_for_bujo_collection(1)

    def dest_for_steno_pad(self, sheet: int) -> str:
        """1-based single-face dest, e.g. ``steno-2026-01``."""
        if self.steno_sheets < 1:
            raise ConfigError("steno_sheets must be >= 1 to name a pad dest")
        if not 1 <= sheet <= self.steno_sheets:
            raise ConfigError(f"steno sheet out of range: {sheet}")
        return _dest(t"steno-{self.year:04d}-{sheet:02d}")

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
        meetings = data.get("meetings")
        meetings_table = meetings if isinstance(meetings, dict) else {}
        tasks = data.get("tasks")
        tasks_table = tasks if isinstance(tasks, dict) else {}
        engineering = data.get("engineering")
        engineering_table = engineering if isinstance(engineering, dict) else {}
        steno = data.get("steno")
        steno_table = steno if isinstance(steno, dict) else {}
        bujo_index_pages, bujo_collections = _parse_bujo(data)
        return cls(
            year=int(data.get("year", 2026)),
            device=str(data.get("device", "supernote-nomad")),
            week_start=str(data.get("week_start", "monday")).lower(),
            months=_parse_months(data),
            title=str(data.get("title", "Year planner")),
            book=str(data.get("book", "year-planner")),
            schedule_from=int(
                daily_table.get("schedule_from", data.get("schedule_from", 7))
            ),
            schedule_to=int(
                daily_table.get("schedule_to", data.get("schedule_to", 16))
            ),
            notes_pages=int(notes_pages),
            habit_columns=_habit_columns(data, habits_table),
            priority_rows=int(
                daily_table.get("priority_rows", data.get("priority_rows", 6))
            ),
            project_cards=int(
                projects_table.get("cards", data.get("project_cards", 3))
            ),
            project_tasks=int(
                projects_table.get("tasks", data.get("project_tasks", 4))
            ),
            project_tickets=int(
                projects_table.get(
                    "tickets_per_page",
                    projects_table.get("tickets", data.get("project_tickets", 8)),
                )
            ),
            project_index_pages=int(
                projects_table.get("index_pages", data.get("project_index_pages", 1))
            ),
            meeting_index_rows=int(
                meetings_table.get("index_rows", data.get("meeting_index_rows", 16))
            ),
            task_rows=int(tasks_table.get("rows", data.get("task_rows", 6))),
            engineering_sheets=int(
                engineering_table.get("sheets", data.get("engineering_sheets", 0))
            ),
            steno_sheets=int(steno_table.get("sheets", data.get("steno_sheets", 0))),
            outline=_parse_bool(data.get("outline", False), "outline"),
            bujo_index_pages=bujo_index_pages,
            bujo_collections=bujo_collections,
            type_overlay=_parse_typography(data),
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
