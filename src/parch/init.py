"""Emit a commented starter TOML of Spec defaults.

``parch init`` is the no-checkout, no-prompt path: values come from
``Spec()`` / ``from_mapping`` defaults, not from examples/ or questionary.
"""

from __future__ import annotations

import argparse
import sys
from datetime import time
from pathlib import Path

from parch import ConfigError
from parch.devices import known_device_ids
from parch.spec import _BOOK_CHOICES, _WEEK_STARTS, Spec


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


def _schedule_toml(spec: Spec) -> str:
    """Preferred ``[daily] schedule`` spelling from ``Bound.as_table``."""
    raw = spec.schedule.as_table()
    pairs: dict[str, object] = {"from": raw["from"], "to": raw["to"]}
    if "step" in raw:
        pairs["step"] = raw["step"]
    return _toml_inline(pairs)


def starter_toml(spec: Spec | None = None) -> str:
    """Readable starter whose live keys round-trip through ``from_mapping``.

    Optional extras (title, favorites, pads, bujo, typography) stay commented
    so ``tomllib.loads`` + ``Spec.from_mapping`` equals ``Spec()``.
    """
    spec = Spec() if spec is None else spec
    devices = ", ".join(known_device_ids())
    weeks = " or ".join(_WEEK_STARTS)
    return f"""\
# parch starter — Spec() defaults. Edit, then:
#   parch init -o planner.toml
#   parch press planner.toml -o planner.pdf
# No checkout. No prompts. Sample jobs also live in examples/ (clone only).

# Calendar year pressed into dest names (year-{spec.year:04d}, month-{spec.year:04d}-01, …).
year = {spec.year}

# Device id: {devices} (aliases: nomad, scribe).
device = {_toml_str(spec.device)}

# Week grid start: {weeks}.
week_start = {_toml_str(spec.week_start)}

# Closed month table (ints 1–12). Omit for the full year.
# List form [1, 3] keeps gaps. month = 7 is a single month.
months = {_months_toml(spec.months)}

# year-planner brow / sibling headline. Omit keeps paint.
# title = "Year planner"

# {_BOOK_CHOICES}
book = {_toml_str(spec.book)}

# Reader sidebar outline (bookmarks). Cover is skipped.
outline = {_toml_bool(spec.outline)}

# Optional extras (default off).
# favorites = true
# my_100 = true
# checkoff_365 = true

[daily]
# Hourly well: floor from, ceil to. Optional step is Clock grain (minutes).
# daily.schedule is a tomlrange Clock bound, not a pair of ints.
schedule = {_schedule_toml(spec)}
notes_pages = {spec.notes_pages}
priority_rows = {spec.priority_rows}

[habits]
columns = {spec.habit_columns}

[projects]
cards = {spec.project_cards}
tickets = {spec.project_tickets}
index_pages = {spec.project_index_pages}

[meetings]
index_rows = {spec.meeting_index_rows}

[tasks]
rows = {spec.task_rows}

# Sibling pads / books — omit keeps year-planner press.
# engineering-notebook requires engineering.sheets >= 1.
# [engineering]
# sheets = {spec.engineering_sheets}
#
# [steno]
# sheets = {spec.steno_sheets}
#
# [bujo]
# index_pages = {spec.bujo_index_pages}
# collections = {spec.bujo_collections}

# [typography.overlay]
# schema_version = 1
# Closed TypeSteps only. Omit keeps the empty overlay.
"""


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
