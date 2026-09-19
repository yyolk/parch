"""Emit a commented starter TOML of Spec defaults.

``parch init`` is the no-checkout, no-prompt path: values come from
``Spec()`` / ``from_mapping`` defaults, not from examples/ or questionary.

The starter is a walk of sealed ``from_mapping`` paths aligned with
``dataclasses.fields(Spec)``. Comments live in ``_COMMENTS`` (path → prose).
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import fields
from datetime import time
from pathlib import Path

from parch import ConfigError
from parch.devices import known_device_ids
from parch.fonts import TypeOverlay
from parch.spec import _BOOK_CHOICES, _WEEK_STARTS, Spec

# Sealed from_mapping paths in emit order, each aligned with one Spec field.
_PATH_FIELD: dict[str, str] = {
    "year": "year",
    "device": "device",
    "week_start": "week_start",
    "months": "months",
    "title": "title",
    "book": "book",
    "outline": "outline",
    "favorites": "favorites_pages",
    "my_100": "my_100",
    "checkoff_365": "checkoff_365",
    "daily.schedule": "schedule",
    "daily.notes_pages": "notes_pages",
    "daily.priority_rows": "priority_rows",
    "habits.columns": "habit_columns",
    "projects.cards": "project_cards",
    "projects.tickets": "project_tickets",
    "projects.index_pages": "project_index_pages",
    "meetings.index_rows": "meeting_index_rows",
    "tasks.rows": "task_rows",
    "engineering.sheets": "engineering_sheets",
    "steno.sheets": "steno_sheets",
    "bujo.index_pages": "bujo_index_pages",
    "bujo.collections": "bujo_collections",
    "typography.overlay.schema_version": "type_overlay",
}

# Root extras stay adjacent (no blank between) when they are commented out.
_ROOT_GROUP = frozenset({"favorites", "my_100", "checkoff_365"})

# Path / section → comment. Values are never stored here — only prose.
_COMMENTS: dict[str, str] = {
    "": (
        "parch starter — Spec() defaults. Edit, then:\n"
        "  parch init -o planner.toml\n"
        "  parch press planner.toml -o planner.pdf\n"
        "No checkout. No prompts. Sample jobs also live in examples/ (clone only)."
    ),
    "year": (
        "Calendar year pressed into dest names "
        "(year-{year:04d}, month-{year:04d}-01, …)."
    ),
    "device": (f"Device id: {', '.join(known_device_ids())} (aliases: nomad, scribe)."),
    "week_start": f"Week grid start: {' or '.join(_WEEK_STARTS)}.",
    "months": (
        "Closed month table (ints 1–12). Omit for the full year.\n"
        "List form [1, 3] keeps gaps. month = 7 is a single month."
    ),
    "title": "year-planner brow / sibling headline. Omit keeps paint.",
    "book": _BOOK_CHOICES,
    "outline": "Reader sidebar outline (bookmarks). Cover is skipped.",
    "favorites": "Optional extras (default off).",
    "daily.schedule": (
        "Hourly well: floor from, ceil to. Optional step is Clock grain (minutes).\n"
        "daily.schedule is a tomlrange Clock bound, not a pair of ints."
    ),
    "engineering": (
        "Sibling pads / books — omit keeps year-planner press.\n"
        "engineering-notebook requires engineering.sheets >= 1."
    ),
    "typography.overlay": "Closed TypeSteps only. Omit keeps the empty overlay.",
}


def _toml_bool(value: bool) -> str:
    return "true" if value else "false"


def _toml_str(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _toml_time(value: time) -> str:
    return f"{value.hour:02d}:{value.minute:02d}:{value.second:02d}"


def _toml_inline(pairs: dict[str, object]) -> str:
    """``{ key = value, … }`` — ints, bools, times, and strings only."""
    parts: list[str] = []
    for key, raw in pairs.items():
        match raw:
            case bool() as flag:
                rendered = _toml_bool(flag)
            case time() as clock:
                rendered = _toml_time(clock)
            case str() as text:
                rendered = _toml_str(text)
            case int() as number:
                rendered = str(number)
            case _:
                raise TypeError(f"unsupported starter value for {key!r}: {type(raw)!r}")
        parts.append(f"{key} = {rendered}")
    return "{ " + ", ".join(parts) + " }"


def _months_toml(months: tuple[int, ...]) -> str:
    """Closed ``{ from, to }`` when contiguous; otherwise a list."""
    if months and months == tuple(range(months[0], months[-1] + 1)):
        return _toml_inline({"from": months[0], "to": months[-1]})
    return "[" + ", ".join(str(month) for month in months) + "]"


def _schedule_toml(schedule: object) -> str:
    """Preferred ``[daily] schedule`` spelling from ``Bound.as_table``."""
    raw = schedule.as_table()  # Bound[time]
    pairs: dict[str, object] = {"from": raw["from"], "to": raw["to"]}
    if "step" in raw:
        pairs["step"] = raw["step"]
    return _toml_inline(pairs)


def _extract(path: str, raw: object) -> object:
    """Live Spec field → TOML-facing value for ``path``."""
    match path:
        case "favorites":
            return bool(raw)
        case "typography.overlay.schema_version":
            return raw.schema_version
        case _:
            return raw


def _live(spec: Spec) -> dict[str, object]:
    """Walk ``Spec`` fields and key the values by sealed from_mapping path."""
    field_to_path = {name: path for path, name in _PATH_FIELD.items()}
    missing = [item.name for item in fields(Spec) if item.name not in field_to_path]
    if missing:
        raise RuntimeError(f"starter walk is missing Spec fields: {', '.join(missing)}")
    extra = sorted(set(field_to_path) - {item.name for item in fields(Spec)})
    if extra:
        raise RuntimeError(f"starter walk has unknown Spec fields: {', '.join(extra)}")
    values: dict[str, object] = {}
    for item in fields(Spec):
        path = field_to_path[item.name]
        values[path] = _extract(path, getattr(spec, item.name))
    return values


def _omitted(path: str, spec: Spec) -> bool:
    """Optional extras stay commented so default starters still equal ``Spec()``."""
    match path:
        case "title":
            return spec.title is None
        case "favorites":
            return spec.favorites_pages == 0
        case "my_100":
            return not spec.my_100
        case "checkoff_365":
            return not spec.checkoff_365
        case "engineering.sheets":
            return spec.engineering_sheets == 0
        case "steno.sheets":
            return spec.steno_sheets == 0
        case "bujo.index_pages" | "bujo.collections":
            return spec.book != "bullet-journal"
        case "typography.overlay.schema_version":
            return spec.type_overlay == TypeOverlay()
        case _:
            return False


def _section_omitted(section: str, spec: Spec) -> bool:
    if not section:
        return False
    return all(
        _omitted(path, spec)
        for path in _PATH_FIELD
        if path == section or path.startswith(f"{section}.")
    )


def _format_comment(text: str, year: int) -> str:
    if "{year" in text:
        return text.format(year=year)
    return text


def _comment_lines(lines: list[str], text: str, year: int) -> None:
    for line in _format_comment(text, year).splitlines():
        lines.append("#" if line == "" else f"# {line}")


def _render(path: str, raw: object) -> str:
    match path:
        case "months":
            return _months_toml(raw)  # type: ignore[arg-type]
        case "daily.schedule":
            return _schedule_toml(raw)
    match raw:
        case bool() as flag:
            return _toml_bool(flag)
        case time() as clock:
            return _toml_time(clock)
        case str() as text:
            return _toml_str(text)
        case int() as number:
            return str(number)
        case _:
            raise TypeError(f"unsupported starter value for {path!r}: {type(raw)!r}")


def _next_path(path: str) -> str | None:
    paths = tuple(_PATH_FIELD)
    index = paths.index(path)
    if index + 1 >= len(paths):
        return None
    return paths[index + 1]


def starter_toml(spec: Spec | None = None) -> str:
    """Readable starter whose live keys round-trip through ``from_mapping``.

    Optional extras (title, favorites, pads, bujo, typography) stay commented
    so ``tomllib.loads`` + ``Spec.from_mapping`` equals ``Spec()``.
    """
    spec = Spec() if spec is None else spec
    live = _live(spec)
    lines: list[str] = []
    _comment_lines(lines, _COMMENTS[""], spec.year)
    lines.append("")
    current = ""
    for path in _PATH_FIELD:
        section, _, key = path.rpartition(".")
        if section != current:
            if lines[-1] != "":
                lines.append("")
            if section:
                if text := _COMMENTS.get(section):
                    _comment_lines(lines, text, spec.year)
                header = f"[{section}]"
                lines.append(
                    f"# {header}" if _section_omitted(section, spec) else header
                )
            current = section
        if text := _COMMENTS.get(path):
            _comment_lines(lines, text, spec.year)
        if path == "title" and spec.title is None:
            lines.append("")
            continue
        prefix = "# " if _omitted(path, spec) else ""
        lines.append(f"{prefix}{key} = {_render(path, live[path])}")
        if not section:
            nxt = _next_path(path)
            if path not in _ROOT_GROUP or nxt not in _ROOT_GROUP:
                lines.append("")
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def write_starter(path: Path, *, force: bool = False, spec: Spec | None = None) -> Path:
    """Write ``starter_toml`` to ``path``. Refuses to clobber unless ``force``."""
    if path.exists() and not force:
        raise ConfigError(f"{path} exists (pass --force to overwrite)")
    path.write_text(starter_toml(spec), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="parch init",
        description="Write a commented starter TOML of Spec defaults (no prompts).",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Write starter TOML here. Default: stdout.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing --output file.",
    )
    args = parser.parse_args(argv)
    text = starter_toml()
    if args.output:
        try:
            dest = write_starter(Path(args.output), force=args.force)
        except ConfigError as exc:
            print(f"parch: {exc}", file=sys.stderr)
            return 2
        print(dest)
        return 0
    sys.stdout.write(text)
    if not text.endswith("\n"):
        sys.stdout.write("\n")
    return 0
