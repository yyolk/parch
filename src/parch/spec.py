"""Tiny press spec — TOML or defaults."""

import tomllib
from dataclasses import dataclass, field
from datetime import date, time
from pathlib import Path
from string.templatelib import Interpolation, Template

from tomlrange import Bound, Clock, Domain, TomlRangeError

from parch import ConfigError
from parch.calendar import quarter_of, year_days
from parch.components.bujo import FUTURE_LOG_MONTHS_PER_PAGE
from parch.fonts.ramp import TYPE_STEPS, TypeOverlay, require_overlay

_WEEK_STARTS = {"monday": 0, "sunday": 6}
_MIX_BOOK = "lined-dot-grid-mix-notebook"
_MIX_BOOK_ALIAS = "lined-dotgrid-notebook"
_PAIR_ORDERS = frozenset({"lined-dot-grid", "dot-grid-lined"})
_BOOKS = frozenset(
    {
        "year-planner",
        "projects-notebook",
        "engineering-notebook",
        "dot-grid-notebook",
        "lined-notebook",
        _MIX_BOOK,
        _MIX_BOOK_ALIAS,
        "bullet-journal",
    }
)
_BOOK_CHOICES = (
    "year-planner, projects-notebook, engineering-notebook, "
    "bullet-journal, dot-grid-notebook, lined-notebook, or "
    "lined-dot-grid-mix-notebook"
)
_EXCLUSIVE_NOTEBOOKS = frozenset(
    {
        "engineering-notebook",
        "dot-grid-notebook",
        "lined-notebook",
    }
)
_TYPOGRAPHY_KEYS = frozenset({"overlay"})
_BUJO_KEYS = frozenset({"index_pages", "collections"})
_DEFAULT_SCHEDULE = Clock.parse({"from": time(7, 0, 0), "to": time(16, 0, 0)})
# Calendar months: closed int domain 1–12. Not Clock (time-of-day).
_MONTH = Domain(int, lo=1, hi=12, name="month")
_DEFAULT_MONTHS = tuple(_MONTH.full())

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
    """List of ints, ``{ from, to }`` via tomlrange, omit (full year), or ``month``.

    Table form is a Bound on the private calendar-month domain (ints 1–12).
    Expansion is ``tuple(bound)`` — Bound walk, not a hand-rolled ``range``.
    ``TomlRangeError`` becomes ``ConfigError`` here. List / ``month`` stay
    discrete tuples so non-contiguous ``[1, 3]`` still works.
    """
    raw = data.get("months")
    if isinstance(raw, list):
        return tuple(int(month) for month in raw)
    if raw is None:
        if "month" in data:
            return (int(data["month"]),)
        return _DEFAULT_MONTHS
    try:
        return tuple(_MONTH.bound(raw, path="months"))
    except TomlRangeError as exc:
        raise ConfigError(str(exc)) from exc


def _hours_from_schedule(bound: Bound[time]) -> tuple[int, ...]:
    """Whole-hour labels for the daily well: floor ``from``, ceil ``to`` (capped at 23).

    Painter bands stay hourly. Bound walk / ``elapsed`` use Clock grain (default
    one minute, or table ``step`` minutes) and are not the hour-label source.
    """
    start_hour = bound.start.hour
    stop = bound.stop
    if stop.minute or stop.second or stop.microsecond:
        stop_hour = min(stop.hour + 1, 23)
    else:
        stop_hour = stop.hour
    return tuple(range(start_hour, stop_hour + 1))


def _parse_schedule(daily_table: TomlTable) -> Bound[time]:
    """``[daily] schedule`` via ``Clock.parse``; omit keeps 07:00–16:00.

    Optional table ``step`` is Clock grain: a positive int (minutes) or a
    naive local time as length-since-midnight. ``as_table`` emits the int
    count. Overlap / merge / adjacent stay on Bound/Bounds.
    """
    raw = daily_table.get("schedule")
    if raw is None:
        return _DEFAULT_SCHEDULE
    try:
        return Clock.parse(raw, path="daily.schedule")
    except TomlRangeError as exc:
        raise ConfigError(str(exc)) from exc


def _parse_work_hours(daily_table: TomlTable) -> Bound[time] | None:
    """Optional ``[daily] work_hours`` via ``Clock.parse``; omit means no shade.

    Same Clock table as ``schedule`` (``from`` / ``to``, optional ``step``).
    Shade is ``hour_shade`` Bound overlap, not a Spec-side hour cache.
    """
    raw = daily_table.get("work_hours")
    if raw is None:
        return None
    try:
        return Clock.parse(raw, path="daily.work_hours")
    except TomlRangeError as exc:
        raise ConfigError(str(exc)) from exc


def _parse_bool(raw: object, key: str) -> bool:
    """Closed boolean TOML field — strings and ints fail loudly."""
    if not isinstance(raw, bool):
        raise ConfigError(f"{key} must be a boolean")
    return raw


def _parse_top_clearance(data: TomlTable) -> float | None:
    """Optional reserved-band override in mm. Omit keeps the Device default.

    ``0`` means no top band. Bools fail — TOML ``true`` is not ``1``.
    """
    if "top_clearance" not in data:
        return None
    raw = data["top_clearance"]
    if isinstance(raw, bool) or not isinstance(raw, int | float):
        raise ConfigError("top_clearance must be a number")
    return float(raw)


def _parse_favorites_pages(data: TomlTable) -> int:
    """``favorites_pages`` count, or ``favorites`` bool. Default 0 (off)."""
    if "favorites_pages" in data:
        return int(data["favorites_pages"])
    if "favorites" in data:
        return 1 if _parse_bool(data["favorites"], "favorites") else 0
    return 0


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


def _toml_str(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _toml_bool(value: bool) -> str:
    return "true" if value else "false"


def _toml_time(value: time) -> str:
    return format(value, "%H:%M:%S")


def _toml_number(value: float) -> str:
    return str(int(value)) if value == int(value) else str(value)


def _months_payload(months: tuple[int, ...]) -> dict[str, int] | list[int]:
    """Contiguous window → ``{ from, to }``; otherwise a discrete int list."""
    lo, hi = months[0], months[-1]
    if months == tuple(range(lo, hi + 1)):
        return {"from": lo, "to": hi}
    return list(months)


def _months_toml(months: tuple[int, ...]) -> str:
    payload = _months_payload(months)
    if isinstance(payload, dict):
        return f"{{ from = {payload['from']}, to = {payload['to']} }}"
    return "[" + ", ".join(str(month) for month in payload) + "]"


def _schedule_toml(bound: Bound[time]) -> str:
    table = bound.as_table()
    parts = [
        f"from = {_toml_time(table['from'])}",
        f"to = {_toml_time(table['to'])}",
    ]
    step = table.get("step")
    if step is not None:
        parts.append(f"step = {step}")
    return "{ " + ", ".join(parts) + " }"


def _overlay_mapping(overlay: TypeOverlay) -> TomlTable | None:
    patches = {
        step: patch for step in TYPE_STEPS if (patch := overlay.patch(step)) is not None
    }
    if not patches:
        return None
    table: TomlTable = {"schema_version": overlay.schema_version}
    for step, patch in patches.items():
        entry: TomlTable = {}
        if patch.size is not None:
            entry["size"] = float(patch.size)
        if patch.weight is not None:
            entry["weight"] = patch.weight
        table[step] = entry
    return table


def _overlay_toml(overlay: TypeOverlay) -> list[str]:
    table = _overlay_mapping(overlay)
    if table is None:
        return []
    lines = [
        "[typography.overlay]",
        f"schema_version = {table['schema_version']}",
        "",
    ]
    for step in TYPE_STEPS:
        raw = table.get(step)
        if not isinstance(raw, dict):
            continue
        lines.append(f"[typography.overlay.{step}]")
        if "size" in raw:
            lines.append(f"size = {_toml_number(float(raw['size']))}")
        if "weight" in raw:
            lines.append(f"weight = {_toml_str(str(raw['weight']))}")
        lines.append("")
    return lines


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
    top_clearance: float | None = None  # mm override; None keeps Device default
    week_start: str = "monday"
    months: tuple[int, ...] = _DEFAULT_MONTHS
    title: str | None = None  # year-planner brow / sibling headline; omit keeps paint
    book: str = "year-planner"
    schedule: Bound[time] = _DEFAULT_SCHEDULE
    work_hours: Bound[time] | None = None  # optional Clock Bound; omit → no daily shade
    notes_pages: int = 2
    habit_columns: int = 10
    priority_rows: int = 6
    project_cards: int = 3
    project_tickets: int = 8
    project_index_pages: int = 1
    meeting_index_rows: int = 16
    task_rows: int = 6  # toml floor; dest paint derives the fitted count
    engineering_sheets: int = 0  # duplex fronts+backs; 0 keeps year-planner press
    steno_sheets: int = 0  # single-face Gregg pages; 0 keeps year-planner press
    dotgrid_sheets: int = 0  # full-bleed clone-dot pages; 0 keeps year-planner press
    lined_sheets: int = 0  # full-bleed lined pages; 0 keeps year-planner press
    lined_dot_grid_sheets: int = 0  # duplex lined front / dot-grid back
    dot_grid_lined_sheets: int = 0  # duplex dot-grid front / lined back
    outline: bool = False  # reader sidebar outline; default off
    favorites_pages: int = 0  # 0 keeps year-planner press; 1 adds favorites-{year}
    my_100: bool = False  # optional My 100 list; default off
    checkoff_365: bool = False  # optional year check-off sheet; default off
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
        if self.book == _MIX_BOOK_ALIAS:
            object.__setattr__(self, "book", _MIX_BOOK)
        if self.top_clearance is not None and self.top_clearance < 0:
            raise ConfigError("top_clearance must be >= 0")
        if self.book == "engineering-notebook" and self.engineering_sheets < 1:
            raise ConfigError("engineering-notebook requires engineering_sheets >= 1")
        if self.book == "engineering-notebook" and self.steno_sheets:
            raise ConfigError("engineering-notebook cannot set steno_sheets")
        if self.book == "engineering-notebook" and self.dotgrid_sheets:
            raise ConfigError("engineering-notebook cannot set dotgrid_sheets")
        if self.book == "engineering-notebook" and self.lined_sheets:
            raise ConfigError("engineering-notebook cannot set lined_sheets")
        if self.book == "dot-grid-notebook" and self.dotgrid_sheets < 1:
            raise ConfigError("dot-grid-notebook requires dotgrid_sheets >= 1")
        if self.book == "dot-grid-notebook" and self.engineering_sheets:
            raise ConfigError("dot-grid-notebook cannot set engineering_sheets")
        if self.book == "dot-grid-notebook" and self.steno_sheets:
            raise ConfigError("dot-grid-notebook cannot set steno_sheets")
        if self.book == "dot-grid-notebook" and self.lined_sheets:
            raise ConfigError("dot-grid-notebook cannot set lined_sheets")
        if (
            self.book == "year-planner"
            and self.lined_dot_grid_sheets
            and self.dot_grid_lined_sheets
        ):
            raise ConfigError(
                "year-planner cannot set both lined_dot_grid_sheets and "
                "dot_grid_lined_sheets"
            )
        _pair = self.lined_dot_grid_sheets or self.dot_grid_lined_sheets
        if (
            self.book == "year-planner"
            and self.lined_sheets
            and (
                self.engineering_sheets
                or self.steno_sheets
                or self.dotgrid_sheets
                or _pair
            )
        ):
            raise ConfigError(
                "year-planner cannot mix lined_sheets with other pad counts"
            )
        if (
            self.book == "year-planner"
            and _pair
            and (
                self.engineering_sheets
                or self.steno_sheets
                or self.dotgrid_sheets
                or self.lined_sheets
            )
        ):
            raise ConfigError(
                "year-planner cannot mix duplex lined/dot-grid sheets with other "
                "pad counts"
            )
        if self.book == "lined-notebook" and self.lined_sheets < 1:
            raise ConfigError("lined-notebook requires lined_sheets >= 1")
        if self.book == "lined-notebook" and self.engineering_sheets:
            raise ConfigError("lined-notebook cannot set engineering_sheets")
        if self.book == "lined-notebook" and self.steno_sheets:
            raise ConfigError("lined-notebook cannot set steno_sheets")
        if self.book == "lined-notebook" and self.dotgrid_sheets:
            raise ConfigError("lined-notebook cannot set dotgrid_sheets")
        if self.book == _MIX_BOOK and not (
            self.lined_dot_grid_sheets or self.dot_grid_lined_sheets
        ):
            raise ConfigError(
                f"{_MIX_BOOK} requires lined_dot_grid_sheets or dot_grid_lined_sheets"
            )
        if self.book == _MIX_BOOK and self.lined_sheets:
            raise ConfigError(f"{_MIX_BOOK} cannot set lined_sheets")
        if self.book == _MIX_BOOK and self.dotgrid_sheets:
            raise ConfigError(f"{_MIX_BOOK} cannot set dotgrid_sheets")
        if self.book == _MIX_BOOK and self.engineering_sheets:
            raise ConfigError(f"{_MIX_BOOK} cannot set engineering_sheets")
        if self.book == _MIX_BOOK and self.steno_sheets:
            raise ConfigError(f"{_MIX_BOOK} cannot set steno_sheets")
        if self.book in _EXCLUSIVE_NOTEBOOKS and self.lined_dot_grid_sheets:
            raise ConfigError(f"{self.book} cannot set lined_dot_grid_sheets")
        if self.book in _EXCLUSIVE_NOTEBOOKS and self.dot_grid_lined_sheets:
            raise ConfigError(f"{self.book} cannot set dot_grid_lined_sheets")
        if not self.months:
            raise ConfigError("months must not be empty")
        seen: set[int] = set()
        for month in self.months:
            if not 1 <= month <= 12:
                raise ConfigError(f"month out of range: {month}")
            if month in seen:
                raise ConfigError(f"duplicate month {month}")
            seen.add(month)
        if self.notes_pages < 0:
            raise ConfigError("notes_pages must be >= 0")
        if not 4 <= self.habit_columns <= 16:
            raise ConfigError("habit_columns must be 4–16")
        if not 4 <= self.priority_rows <= 8:
            raise ConfigError("priority_rows must be 4–8")
        if not 2 <= self.project_cards <= 4:
            raise ConfigError("project_cards must be 2–4")
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
        if not 0 <= self.dotgrid_sheets <= 100:
            raise ConfigError("dotgrid_sheets must be 0–100")
        if not 0 <= self.lined_sheets <= 100:
            raise ConfigError("lined_sheets must be 0–100")
        if not 0 <= self.lined_dot_grid_sheets <= 100:
            raise ConfigError("lined_dot_grid_sheets must be 0–100")
        if not 0 <= self.dot_grid_lined_sheets <= 100:
            raise ConfigError("dot_grid_lined_sheets must be 0–100")
        if not 0 <= self.favorites_pages <= 1:
            raise ConfigError("favorites_pages must be 0–1")
        if not 1 <= self.bujo_index_pages <= 6:
            raise ConfigError("bujo index_pages must be 1–6")
        if not 0 <= self.bujo_collections <= 48:
            raise ConfigError("bujo collections must be 0–48")

    @property
    def schedule_hours(self) -> tuple[int, ...]:
        """Hour labels for the daily well: floor ``from``, ceil ``to``."""
        return _hours_from_schedule(self.schedule)

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
    def year_day_count(self) -> int:
        """365 or 366 from ``self.year`` — February length, not a hardcoded 365."""
        return year_days(self.year)

    @property
    def favorites_dest(self) -> str:
        """Year-scoped Favorites dest, e.g. ``favorites-2026``. Emitted only when enabled."""
        return _dest(t"favorites-{self.year:04d}")

    @property
    def checkoff_365_dest(self) -> str:
        """Optional sheet dest, e.g. ``checkoff-365-2026``. Name keeps 365 as the product id."""
        return _dest(t"checkoff-365-{self.year:04d}")

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

    @property
    def my_100_dest(self) -> str:
        """My 100 landing — page 1."""
        return self.dest_for_my_100(1)

    def dest_for_my_100(self, page: int) -> str:
        """Page 1 is ``my-100-{year}``; later pages append ``-{page:02d}``."""
        if page < 1:
            raise ConfigError(f"my 100 page must be >= 1, not {page}")
        if page == 1:
            return _dest(t"my-100-{self.year:04d}")
        return _dest(t"my-100-{self.year:04d}-{page:02d}")

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

    def dest_for_dotgrid_pad(self, sheet: int) -> str:
        """1-based single-face dest, e.g. ``dotgrid-2026-01``."""
        if self.dotgrid_sheets < 1:
            raise ConfigError("dotgrid_sheets must be >= 1 to name a pad dest")
        if not 1 <= sheet <= self.dotgrid_sheets:
            raise ConfigError(f"dotgrid sheet out of range: {sheet}")
        return _dest(t"dotgrid-{self.year:04d}-{sheet:02d}")

    def dest_for_lined_pad(self, sheet: int) -> str:
        """1-based single-face dest, e.g. ``lined-2026-01``."""
        if self.lined_sheets < 1:
            raise ConfigError("lined_sheets must be >= 1 to name a pad dest")
        if not 1 <= sheet <= self.lined_sheets:
            raise ConfigError(f"lined sheet out of range: {sheet}")
        return _dest(t"lined-{self.year:04d}-{sheet:02d}")

    def dest_for_duplex_pair_pad(self, order: str, sheet: int, face: str) -> str:
        """1-based duplex dest, e.g. ``lined-dot-grid-2026-01-front``."""
        if order not in _PAIR_ORDERS:
            raise ConfigError(
                "duplex pair order must be lined-dot-grid or dot-grid-lined, "
                f"not {order!r}"
            )
        if face not in {"front", "back"}:
            raise ConfigError(f"duplex pair face must be front or back, not {face!r}")
        count = (
            self.lined_dot_grid_sheets
            if order == "lined-dot-grid"
            else self.dot_grid_lined_sheets
        )
        label = (
            "lined_dot_grid_sheets"
            if order == "lined-dot-grid"
            else "dot_grid_lined_sheets"
        )
        if count < 1:
            raise ConfigError(f"{label} must be >= 1 to name a pad dest")
        if not 1 <= sheet <= count:
            raise ConfigError(f"duplex pair sheet out of range: {sheet}")
        return _dest(t"{order}-{self.year:04d}-{sheet:02d}-{face}")

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
        dotgrid = data.get("dotgrid")
        dotgrid_table = dotgrid if isinstance(dotgrid, dict) else {}
        lined = data.get("lined")
        lined_table = lined if isinstance(lined, dict) else {}
        lined_dot_grid = data.get("lined-dot-grid")
        lined_dot_grid_table = (
            lined_dot_grid if isinstance(lined_dot_grid, dict) else {}
        )
        dot_grid_lined = data.get("dot-grid-lined")
        dot_grid_lined_table = (
            dot_grid_lined if isinstance(dot_grid_lined, dict) else {}
        )
        bujo_index_pages, bujo_collections = _parse_bujo(data)
        return cls(
            year=int(data.get("year", 2026)),
            device=str(data.get("device", "supernote-nomad")),
            top_clearance=_parse_top_clearance(data),
            week_start=str(data.get("week_start", "monday")).lower(),
            months=_parse_months(data),
            title=str(data["title"]) if "title" in data else None,
            book=str(data.get("book", "year-planner")),
            schedule=_parse_schedule(daily_table),
            work_hours=_parse_work_hours(daily_table),
            notes_pages=int(notes_pages),
            habit_columns=_habit_columns(data, habits_table),
            priority_rows=int(
                daily_table.get("priority_rows", data.get("priority_rows", 6))
            ),
            project_cards=int(
                projects_table.get("cards", data.get("project_cards", 3))
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
            dotgrid_sheets=int(
                dotgrid_table.get("sheets", data.get("dotgrid_sheets", 0))
            ),
            lined_sheets=int(lined_table.get("sheets", data.get("lined_sheets", 0))),
            lined_dot_grid_sheets=int(
                lined_dot_grid_table.get("sheets", data.get("lined_dot_grid_sheets", 0))
            ),
            dot_grid_lined_sheets=int(
                dot_grid_lined_table.get("sheets", data.get("dot_grid_lined_sheets", 0))
            ),
            outline=_parse_bool(data.get("outline", False), "outline"),
            favorites_pages=_parse_favorites_pages(data),
            my_100=_parse_bool(data.get("my_100", False), "my_100"),
            checkoff_365=_parse_bool(data.get("checkoff_365", False), "checkoff_365"),
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

    def to_mapping(self) -> TomlTable:
        """Canonical TOML-shaped table of the effective spec.

        Inverse of ``from_mapping`` for the closed tables (not the leftover
        aliases ``from_mapping`` still accepts). ``title`` is omitted when
        unset. ``[typography]`` is omitted when the overlay has no patches.
        """
        data: TomlTable = {
            "year": self.year,
            "device": self.device,
            "week_start": self.week_start,
            "months": _months_payload(self.months),
            "book": self.book,
            "outline": self.outline,
            "favorites": self.favorites_pages == 1,
            "my_100": self.my_100,
            "checkoff_365": self.checkoff_365,
            "daily": {
                "schedule": dict(self.schedule.as_table()),
                "notes_pages": self.notes_pages,
                "priority_rows": self.priority_rows,
            }
            | (
                {"work_hours": dict(self.work_hours.as_table())}
                if self.work_hours is not None
                else {}
            ),
            "habits": {"columns": self.habit_columns},
            "projects": {
                "cards": self.project_cards,
                "tickets": self.project_tickets,
                "index_pages": self.project_index_pages,
            },
            "meetings": {"index_rows": self.meeting_index_rows},
            "tasks": {"rows": self.task_rows},
            "engineering": {"sheets": self.engineering_sheets},
            "steno": {"sheets": self.steno_sheets},
            "dotgrid": {"sheets": self.dotgrid_sheets},
            "lined": {"sheets": self.lined_sheets},
            "lined-dot-grid": {"sheets": self.lined_dot_grid_sheets},
            "dot-grid-lined": {"sheets": self.dot_grid_lined_sheets},
            "bujo": {
                "index_pages": self.bujo_index_pages,
                "collections": self.bujo_collections,
            },
        }
        if self.title is not None:
            data["title"] = self.title
        if self.top_clearance is not None:
            data["top_clearance"] = self.top_clearance
        overlay = _overlay_mapping(self.type_overlay)
        if overlay is not None:
            data["typography"] = {"overlay": overlay}
        return data

    def to_toml(self) -> str:
        """Emit TOML that ``from_path`` / ``from_mapping`` can load back."""
        lines = [
            f"year = {self.year}",
            f"device = {_toml_str(self.device)}",
            f"week_start = {_toml_str(self.week_start)}",
            f"months = {_months_toml(self.months)}",
        ]
        if self.top_clearance is not None:
            lines.append(f"top_clearance = {_toml_number(self.top_clearance)}")
        if self.title is not None:
            lines.append(f"title = {_toml_str(self.title)}")
        lines.extend(
            [
                f"book = {_toml_str(self.book)}",
                f"outline = {_toml_bool(self.outline)}",
                f"favorites = {_toml_bool(self.favorites_pages == 1)}",
                f"my_100 = {_toml_bool(self.my_100)}",
                f"checkoff_365 = {_toml_bool(self.checkoff_365)}",
                "",
                "[daily]",
                f"schedule = {_schedule_toml(self.schedule)}",
            ]
        )
        if self.work_hours is not None:
            lines.append(f"work_hours = {_schedule_toml(self.work_hours)}")
        lines.extend(
            [
                f"notes_pages = {self.notes_pages}",
                f"priority_rows = {self.priority_rows}",
                "",
                "[habits]",
                f"columns = {self.habit_columns}",
                "",
                "[projects]",
                f"cards = {self.project_cards}",
                f"tickets = {self.project_tickets}",
                f"index_pages = {self.project_index_pages}",
                "",
                "[meetings]",
                f"index_rows = {self.meeting_index_rows}",
                "",
                "[tasks]",
                f"rows = {self.task_rows}",
                "",
                "[engineering]",
                f"sheets = {self.engineering_sheets}",
                "",
                "[steno]",
                f"sheets = {self.steno_sheets}",
                "",
                "[dotgrid]",
                f"sheets = {self.dotgrid_sheets}",
                "",
                "[lined]",
                f"sheets = {self.lined_sheets}",
                "",
                "[lined-dot-grid]",
                f"sheets = {self.lined_dot_grid_sheets}",
                "",
                "[dot-grid-lined]",
                f"sheets = {self.dot_grid_lined_sheets}",
                "",
                "[bujo]",
                f"index_pages = {self.bujo_index_pages}",
                f"collections = {self.bujo_collections}",
                "",
            ]
        )
        lines.extend(_overlay_toml(self.type_overlay))
        text = "\n".join(lines)
        return text if text.endswith("\n") else text + "\n"
