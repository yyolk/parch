"""Nomad Topband nav. Scribe keeps Hyperpaper; MOS profiles keep MOS."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from parch.calendar import walk
from parch.calendar.day import Day
from parch.calendar.month import Month
from parch.calendar.quarter import Quarter
from parch.calendar.week import Week
from parch.devices import is_nomad

# Gridwright lock tokens. Device record stays mos 8mm / writing 4mm / toolbar 8mm.
BEZEL = "3mm"
CHROME_H = "6.5mm"
TEMPO_H = "6mm"

# Locked strip order. Notes is not a chip.
STRIP_KEYS = (
    "contents",
    "cal",
    "q",
    "mon",
    "wk",
    "day",
    "tasks",
    "habits",
    "review",
)

STRIP_SECTION = {
    "contents": "index",
    "cal": "annual",
    "q": "quarterly",
    "mon": "monthly",
    "wk": "weekly",
    "day": "daily",
    "tasks": "tasks",
    "habits": "habits",
    "review": "review",
}

# Contents primary (Habits + Review last) then MORE.
CONTENTS_PRIMARY = (
    "annual",
    "quarterly",
    "monthly",
    "weekly",
    "daily",
    "tasks",
    "habits",
    "review",
)
CONTENTS_MORE = ("projects", "meetings", "colophon")
CONTENTS_SKIP = frozenset({"cover", "index", "daily_notes"})

CONTENTS_LABELS = {
    "annual": "Calendar",
    "quarterly": "Quarters",
    "monthly": "Months",
    "weekly": "Weeks",
    "daily": "Days",
    "tasks": "Tasks",
    "habits": "Habits",
    "review": "Review",
    "projects": "Projects",
    "meetings": "Meetings",
    "colophon": "About",
}

_MIN_PACK_ROWS = 12
_MAX_PACK_ROWS = 14
_DEFAULT_WEEKS_PER_PAGE = 13


@dataclass(frozen=True)
class NavContext:
    """Resolved calendar focus for a live page dest."""

    kind: str
    day: Day | None = None
    week: Week | None = None
    month: Month | None = None
    quarter: Quarter | None = None
    tasks_week: Week | None = None
    review_week: Week | None = None


def nomad_topband(configurator) -> bool:
    """Device-gated Topband. Missing / non-Nomad device keeps MOS or Hyperpaper."""
    device = configurator.dig("device") if configurator is not None else None
    if device is None:
        return False
    if hasattr(device, "get"):
        name = device.get("name")
        if name:
            return is_nomad(str(name))
    return is_nomad(str(device))


def enabled_section_names(configurator) -> set[str]:
    return {str(section["name"]) for section in configurator.enabled_sections()}


def strip_keys(configurator) -> list[str]:
    """Enabled Topband keys in locked order. Notes never appears."""
    names = enabled_section_names(configurator)
    keys: list[str] = []
    for key in STRIP_KEYS:
        section = STRIP_SECTION[key]
        if key == "contents":
            if "index" in names:
                keys.append(key)
            continue
        if section in names:
            keys.append(key)
    return keys


def section_name_for_page_id(page_id: str | None) -> str | None:
    """Map a live page dest onto the Topband section that should highlight."""
    if not page_id:
        return None
    if page_id == "index":
        return "index"
    if page_id == "annual":
        return "annual"
    if page_id.startswith("quarter-"):
        return "quarterly"
    if page_id.startswith("month-"):
        return "monthly"
    if page_id.startswith("daily-note-"):
        return "daily"
    if page_id.startswith("habits"):
        return "habits"
    if page_id.startswith("review"):
        return "review"
    if page_id.startswith("tasks"):
        return "tasks"
    if page_id == "projects" or page_id.startswith("project"):
        return None
    if page_id == "meetings" or page_id.startswith("meeting"):
        return None
    if len(page_id) >= 6 and page_id[4] == "W" and page_id[0].isdigit():
        return "weekly"
    if len(page_id) == 10 and page_id[4] == "-" and page_id[7] == "-":
        return "daily"
    return None


def strip_key_for_page_id(page_id: str | None) -> str | None:
    name = section_name_for_page_id(page_id)
    if name == "index":
        return "contents"
    for key, section in STRIP_SECTION.items():
        if section == name:
            return key
    return None


def _weekday_start(configurator) -> str:
    return configurator.weekday_start()


def _day(configurator, raw: date | Day) -> Day:
    if isinstance(raw, Day):
        return raw
    return Day(weekday_start=_weekday_start(configurator), day=raw)


def parse_week_id(week_id: str, configurator) -> Week:
    year = int(week_id[:4])
    number = int(week_id[5:])
    monday = date.fromisocalendar(year, number, 1)
    return Week(weekday_start=_weekday_start(configurator), day=_day(configurator, monday))


def planner_weeks(configurator) -> list[Week]:
    """Weeks spanning the configured month range (same window as Tasks/Review)."""
    start = configurator.start_date().beginning_of_month().beginning_of_week()
    end = configurator.end_date().end_of_month().end_of_week()
    days = list(walk(start, end))
    weeks: list[Week] = []
    weekday_start = _weekday_start(configurator)
    for i in range(0, len(days), 7):
        chunk = days[i : i + 7]
        if not chunk:
            continue
        weeks.append(Week(weekday_start=weekday_start, day=chunk[0]))
    return weeks


def _weeks_per_page(configurator, section: str) -> int:
    for item in configurator.enabled_sections():
        if str(item["name"]) != section:
            continue
        params = item.get("params") or {}
        if hasattr(params, "get"):
            raw = params.get("weeks_per_page")
            if raw:
                return int(raw)
    return _DEFAULT_WEEKS_PER_PAGE


def pack_week_sizes(n_weeks: int, weeks_per_page: int = _DEFAULT_WEEKS_PER_PAGE) -> list[int]:
    n = int(weeks_per_page)
    if n < 1:
        raise ValueError("weeks_per_page must be at least 1")
    if n_weeks <= 0:
        return [0]
    sizes = [n] * (n_weeks // n)
    rem = n_weeks % n
    if rem:
        sizes.append(rem)
    if (
        len(sizes) >= 2
        and sizes[-1] < _MIN_PACK_ROWS
        and sizes[-2] + sizes[-1] <= _MAX_PACK_ROWS
    ):
        sizes[-2] += sizes[-1]
        sizes.pop()
    return sizes


def chunk_weeks(weeks: list[Week], weeks_per_page: int = _DEFAULT_WEEKS_PER_PAGE) -> list[list[Week]]:
    sizes = pack_week_sizes(len(weeks), weeks_per_page)
    out: list[list[Week]] = []
    i = 0
    for size in sizes:
        out.append(weeks[i : i + size])
        i += size
    return out


def tasks_week_id(week: Week) -> str:
    return f"tasks-{week.id}"


def review_week_id(week: Week) -> str:
    return f"review-{week.id}"


def tasks_index_id(page_index: int) -> str:
    return "tasks" if page_index == 0 else f"tasks-{page_index + 1}"


def review_index_id(page_index: int) -> str:
    return "review" if page_index == 0 else f"review-{page_index + 1}"


def habits_month_id(month: Month) -> str:
    return f"habits-{month.name}"


def week_intersects_month(week: Week, month: Month) -> bool:
    return any(day.month() == month for day in week.days())


def week_intersects_quarter(week: Week, quarter: Quarter) -> bool:
    return any(day.quarter() == quarter for day in week.days())


def index_listing_week(
    configurator,
    week: Week,
    *,
    section: str,
) -> str:
    weeks = planner_weeks(configurator)
    chunks = chunk_weeks(weeks, _weeks_per_page(configurator, section))
    ident = tasks_index_id if section == "tasks" else review_index_id
    for index, chunk in enumerate(chunks):
        if any(item == week for item in chunk):
            return ident(index)
    return ident(0)


def _first_week_intersecting(
    configurator,
    *,
    month: Month | None = None,
    quarter: Quarter | None = None,
) -> Week | None:
    for week in planner_weeks(configurator):
        if month is not None and week_intersects_month(week, month):
            return week
        if quarter is not None and week_intersects_quarter(week, quarter):
            return week
    return None


def context_from_page_id(page_id: str | None, configurator) -> NavContext:
    """Parse a page dest into the calendar focus used for contextual jumps."""
    start = configurator.start_date()
    if not page_id:
        return NavContext(kind="unknown", day=start)
    if page_id == "index":
        return NavContext(kind="index", day=start)
    if page_id == "annual":
        return NavContext(kind="annual", day=start, month=start.month(), quarter=start.quarter())
    if page_id.startswith("quarter-"):
        # quarter-2026-1
        parts = page_id.split("-")
        year = int(parts[1])
        number = int(parts[2])
        month_n = (number - 1) * 3 + 1
        day = _day(configurator, date(year, month_n, 1))
        quarter = day.quarter()
        return NavContext(kind="quarterly", day=day, month=day.month(), quarter=quarter)
    if page_id.startswith("month-"):
        day = _day(configurator, date.fromisoformat(page_id[len("month-") :]))
        return NavContext(kind="monthly", day=day, month=day.month(), quarter=day.quarter())
    if page_id.startswith("daily-note-"):
        # daily-note-2026-01-01-page-1
        rest = page_id[len("daily-note-") :]
        iso = rest.rsplit("-page-", 1)[0]
        day = _day(configurator, date.fromisoformat(iso))
        week = day.week()
        return NavContext(
            kind="daily",
            day=day,
            week=week,
            month=day.month(),
            quarter=day.quarter(),
        )
    if page_id.startswith("habits-"):
        name = page_id[len("habits-") :]
        month = _month_named(configurator, name)
        day = month.day
        return NavContext(kind="habits_month", day=day, month=month, quarter=day.quarter())
    if page_id == "habits":
        return NavContext(kind="habits", day=start, month=start.month(), quarter=start.quarter())
    if page_id.startswith("review-") and "W" in page_id:
        week = parse_week_id(page_id[len("review-") :], configurator)
        return NavContext(
            kind="review_week",
            day=week.days()[-1],
            week=week,
            month=week.days()[-1].month(),
            quarter=week.days()[-1].quarter(),
            review_week=week,
        )
    if page_id.startswith("review"):
        return NavContext(kind="review", day=start)
    if page_id.startswith("tasks-") and "W" in page_id:
        week = parse_week_id(page_id[len("tasks-") :], configurator)
        start_day = week.days()[0]
        return NavContext(
            kind="tasks_week",
            day=start_day,
            week=week,
            month=start_day.month(),
            quarter=start_day.quarter(),
            tasks_week=week,
        )
    if page_id.startswith("tasks"):
        return NavContext(kind="tasks", day=start)
    if len(page_id) >= 6 and page_id[4] == "W" and page_id[0].isdigit():
        week = parse_week_id(page_id, configurator)
        start_day = week.days()[0]
        return NavContext(
            kind="weekly",
            day=start_day,
            week=week,
            month=start_day.month(),
            quarter=start_day.quarter(),
        )
    if len(page_id) == 10 and page_id[4] == "-" and page_id[7] == "-":
        day = _day(configurator, date.fromisoformat(page_id))
        week = day.week()
        return NavContext(
            kind="daily",
            day=day,
            week=week,
            month=day.month(),
            quarter=day.quarter(),
        )
    return NavContext(kind="unknown", day=start)


def _month_named(configurator, name: str) -> Month:
    start = configurator.start_date().month()
    end = configurator.end_date().month()
    for month in walk(start, end):
        if month.name == name:
            return month
    day = configurator.start_date().beginning_of_month()
    return Month(weekday_start=_weekday_start(configurator), day=day)


def _focus_week(ctx: NavContext, configurator) -> Week:
    if ctx.week is not None:
        return ctx.week
    day = ctx.day or configurator.start_date()
    return day.week()


def _cross_boundary_day(ctx: NavContext, configurator) -> Day:
    """Tasks uses week start; Review uses week end."""
    if ctx.kind == "review_week" and ctx.week is not None:
        return ctx.week.days()[-1]
    if ctx.kind == "tasks_week" and ctx.week is not None:
        return ctx.week.days()[0]
    if ctx.week is not None:
        return ctx.week.days()[0]
    return ctx.day or configurator.start_date()


def _day_from_context(ctx: NavContext, configurator) -> Day:
    """Topband Day dest: strip-first day, or 1st of the habits month."""
    if ctx.kind in {"tasks_week", "review_week", "weekly"} and ctx.week is not None:
        return ctx.week.days()[0]
    if ctx.kind == "habits_month" and ctx.month is not None:
        return ctx.month.day
    if ctx.kind == "monthly" and ctx.month is not None:
        return ctx.month.day
    if ctx.kind == "quarterly" and ctx.quarter is not None:
        return ctx.quarter.day
    return ctx.day or configurator.start_date()


def strip_dest_id(key: str, page_id: str | None, configurator) -> str:
    """Contextual dest id for a Topband chip. Caller runs it through manifest.dest."""
    ctx = context_from_page_id(page_id, configurator)
    names = enabled_section_names(configurator)
    start = configurator.start_date()

    if key == "contents":
        return "index"
    if key == "cal":
        return "annual"
    if key == "q":
        day = _cross_boundary_day(ctx, configurator)
        return day.quarter().id
    if key == "mon":
        day = _cross_boundary_day(ctx, configurator)
        return day.month().id
    if key == "wk":
        return _focus_week(ctx, configurator).id
    if key == "day":
        return _day_from_context(ctx, configurator).id
    if key == "tasks":
        return _into_week_section(ctx, configurator, section="tasks", names=names)
    if key == "habits":
        return _into_habits(ctx, configurator, names)
    if key == "review":
        return _into_week_section(ctx, configurator, section="review", names=names)
    return start.id


def _into_week_section(
    ctx: NavContext,
    configurator,
    *,
    section: str,
    names: set[str],
) -> str:
    week_id = tasks_week_id if section == "tasks" else review_week_id
    index_id = tasks_index_id if section == "tasks" else review_index_id
    if section not in names:
        return index_id(0)
    if ctx.kind in {"daily", "weekly"} and ctx.week is not None:
        return week_id(ctx.week)
    if ctx.kind in {"tasks_week", "review_week"} and ctx.week is not None:
        return week_id(ctx.week)
    if ctx.kind in {"monthly", "habits_month"} and ctx.month is not None:
        week = _first_week_intersecting(configurator, month=ctx.month)
        if week is not None:
            return index_listing_week(configurator, week, section=section)
        return index_id(0)
    if ctx.kind == "quarterly" and ctx.quarter is not None:
        week = _first_week_intersecting(configurator, quarter=ctx.quarter)
        if week is not None:
            return index_listing_week(configurator, week, section=section)
        return index_id(0)
    return index_id(0)


def _into_habits(ctx: NavContext, configurator, names: set[str]) -> str:
    if "habits" not in names:
        return "habits"
    if ctx.kind == "quarterly" and ctx.quarter is not None:
        return habits_month_id(ctx.quarter.months()[0])
    if ctx.kind in {"monthly", "habits_month"} and ctx.month is not None:
        return habits_month_id(ctx.month)
    if ctx.kind in {"daily", "weekly", "tasks_week", "review_week"}:
        day = ctx.day or configurator.start_date()
        if ctx.kind == "weekly" and ctx.week is not None:
            day = ctx.week.days()[0]
        return habits_month_id(day.month())
    return "habits"


def contents_rows(configurator) -> tuple[list[str], list[str]]:
    """Enabled Contents names: primary (Habits/Review last), then MORE."""
    names = enabled_section_names(configurator)
    primary = [name for name in CONTENTS_PRIMARY if name in names]
    more = [name for name in CONTENTS_MORE if name in names]
    return primary, more


def contents_dest_id(name: str, configurator) -> str:
    """First-page dest for a Contents row."""
    if name == "annual":
        return "annual"
    if name == "quarterly":
        return configurator.start_date().quarter().id
    if name == "monthly":
        return configurator.start_date().month().id
    if name == "weekly":
        first = configurator.start_date().beginning_of_month().beginning_of_week()
        return Week(weekday_start=configurator.weekday_start(), day=first).id
    if name == "daily":
        return configurator.start_date().id
    if name == "tasks":
        return "tasks"
    if name == "habits":
        return "habits"
    if name == "review":
        return "review"
    return name


def prev_next_week(week: Week) -> tuple[Week, Week]:
    prev = Week(weekday_start=week.weekday_start, day=week.day + (-7))
    nxt = Week(weekday_start=week.weekday_start, day=week.day + 7)
    return prev, nxt


def tempo_kind(page_id: str | None) -> str | None:
    """Which tempo pattern a page uses, or None."""
    name = section_name_for_page_id(page_id)
    if name == "daily":
        return "daily"
    if name == "weekly":
        return "weekly"
    if name == "monthly":
        return "monthly"
    if name == "quarterly":
        return "quarterly"
    if name == "habits" and page_id and page_id.startswith("habits-"):
        return "habits"
    if name == "tasks" and page_id and "W" in page_id:
        return "tasks"
    if name == "review" and page_id and "W" in page_id:
        return "review"
    return None


def section_param(configurator, name: str, key: str, default: Any) -> Any:
    for item in configurator.enabled_sections():
        if str(item["name"]) != name:
            continue
        params = item.get("params") or {}
        if hasattr(params, "get") and key in params:
            return params.get(key)
    return default
