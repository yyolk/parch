"""JSON Schema for Spec TOML — editor autocomplete and key docs.

The schema is hand-authored (generation is secondary). Closed enums
(books, devices, TypeSteps, week_start) are read from the runtime
tables so the dump cannot drift from ``Spec`` / overlay validation.

``parch schema`` prints the draft-07 document. ``parch init`` writes a
tiny starter whose first lines are the Taplo ``#:schema`` directive and
the ``#$ schema =`` comment so Even Better TOML / Tombi / VS Code can
resolve a sibling ``spec.schema.json``.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from parch import ConfigError
from parch.devices.registry import _KNOWN
from parch.fonts.ramp import _SIZE_RANGE, _WEIGHTS, OVERLAY_SCHEMA_VERSION, TYPE_STEPS
from parch.spec import _BOOKS, _WEEK_STARTS

SCHEMA_FILENAME = "spec.schema.json"
SCHEMA_COMMENT = f'#$ schema = "{SCHEMA_FILENAME}"'
SCHEMA_DIRECTIVE = f"#:schema {SCHEMA_FILENAME}"
DEFAULT_INIT_NAME = "spec.toml"

type Schema = dict[str, Any]


def _md(text: str) -> dict[str, str]:
    """``description`` plus VS Code ``markdownDescription``."""
    return {"description": text, "markdownDescription": text}


def _int_range(lo: int, hi: int, text: str) -> Schema:
    return {"type": "integer", "minimum": lo, "maximum": hi, **_md(text)}


def _bool(text: str) -> Schema:
    return {"type": "boolean", **_md(text)}


def _month() -> Schema:
    return _int_range(1, 12, "Calendar month (1–12).")


def _local_time() -> Schema:
    return {
        "type": "string",
        **_md(
            "TOML local time (`07:00:00`). After `tomllib` this is "
            "`datetime.time` — not a string. Editors still treat the "
            "lexeme as a time."
        ),
    }


def _from_to_bound(domain: str, value: Schema) -> Schema:
    return {
        "type": "object",
        "required": ["from", "to"],
        "additionalProperties": False,
        "properties": {
            "from": {**value, **_md(f"Inclusive start ({domain}).")},
            "to": {**value, **_md(f"Inclusive end ({domain}).")},
        },
        **_md(f"Closed `{{ from, to }}` table on the {domain} domain."),
    }


def _type_patch(step: str) -> Schema:
    lo, hi = _SIZE_RANGE[step]
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "size": {
                "type": "number",
                "exclusiveMinimum": 0,
                "minimum": lo,
                "maximum": hi,
                **_md(
                    f"Absolute Pt override for `{step}` "
                    f"(closed band {lo:g}–{hi:g}). Does not change "
                    "`root_body` or sibling steps."
                ),
            },
            "weight": {
                "type": "string",
                "enum": sorted(_WEIGHTS),
                **_md("Jost cut: `book` / `medium` / `bold` / `heavy`."),
            },
        },
        **_md(
            f"Optional size and/or weight patch for TypeStep `{step}`. "
            "Omit a field to keep the closed default."
        ),
    }


def _overlay_properties() -> Schema:
    props: Schema = {
        "schema_version": {
            "type": "integer",
            "const": OVERLAY_SCHEMA_VERSION,
            **_md(
                f"Must be exactly `{OVERLAY_SCHEMA_VERSION}` "
                "(OVERLAY_SCHEMA_VERSION). Missing / older / newer fails "
                "the press before paint."
            ),
        }
    }
    for step in TYPE_STEPS:
        props[step] = _type_patch(step)
    return props


def spec_schema() -> Schema:
    """Draft-07 JSON Schema for a parch Spec TOML document."""
    month = _month()
    months_table = _from_to_bound("calendar month", month)
    months_list = {
        "type": "array",
        "minItems": 1,
        "uniqueItems": True,
        "items": month,
        **_md(
            "Discrete month list. May be non-contiguous (`[1, 3]`). "
            "Prefer `{ from, to }` for a contiguous window."
        ),
    }
    schedule_step = {
        "oneOf": [
            {
                "type": "integer",
                "minimum": 1,
                **_md("Clock grain in minutes. `as_table` emits this int."),
            },
            _local_time(),
        ],
        **_md(
            "Optional Clock grain. Positive int (minutes) or a naive "
            "local time as length-since-midnight (`00:30:00`)."
        ),
    }
    schedule = {
        "type": "object",
        "required": ["from", "to"],
        "additionalProperties": False,
        "properties": {
            "from": {
                **_local_time(),
                **_md("Inclusive local start. Default 07:00:00."),
            },
            "to": {**_local_time(), **_md("Inclusive local end. Default 16:00:00.")},
            "step": schedule_step,
        },
        **_md(
            "`[daily] schedule` via tomlrange Clock. Omit the table to "
            "keep 07:00–16:00. Hour labels are floor `from`, ceil `to`."
        ),
    }

    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "https://github.com/yyolk/parch/spec.schema.json",
        "title": "parch Spec",
        **_md(
            "Press job TOML for [parch](https://github.com/yyolk/parch). "
            "Keys here are the editor-facing document — not `Spec` "
            "dataclass field names. Closed tables (`[typography]`, "
            "`[bujo]`) fail on unknown keys; leftover top-level "
            "spellings still parse."
        ),
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "$schema": {
                "type": "string",
                **_md(
                    "Taplo root-key schema URL. `parch init` writes the "
                    f"`{SCHEMA_COMMENT}` comment instead; this key is "
                    "optional and ignored by `Spec.from_mapping`."
                ),
            },
            "year": {
                "type": "integer",
                "examples": [2026],
                **_md("Planner year. Default 2026. Drives dest names (`year-2026`)."),
            },
            "device": {
                "type": "string",
                "enum": sorted(_KNOWN),
                **_md(
                    "Slate id. Canonical: `supernote-nomad`, `kindle-scribe`. "
                    "Aliases: `nomad`, `scribe`. Default `supernote-nomad`."
                ),
            },
            "week_start": {
                "type": "string",
                "enum": sorted(_WEEK_STARTS),
                **_md("`monday` (ISO weeks) or `sunday`. Default `monday`."),
            },
            "months": {
                "oneOf": [months_table, months_list],
                **_md(
                    "Pressed months. Omit for the full year (1–12). "
                    "Table form `{ from, to }` is a tomlrange Bound on "
                    "the calendar-month domain. List form stays discrete "
                    "so `[1, 3]` works. Empty list fails."
                ),
            },
            "month": {
                **month,
                **_md(
                    "Singleton month when `months` is omitted. Leftover "
                    "spelling — prefer `months = { from = N, to = N }` "
                    "or `months = [N]`."
                ),
            },
            "title": {
                "type": "string",
                **_md(
                    "Cover brow / sibling headline. Omit keeps painter "
                    "defaults (`Year planner`, `Projects`, …)."
                ),
            },
            "book": {
                "type": "string",
                "enum": sorted(_BOOKS),
                **_md(
                    "Book kind. Default `year-planner`. "
                    "`engineering-notebook` requires `[engineering] sheets >= 1`."
                ),
            },
            "outline": _bool(
                "Reader sidebar outline (PDF bookmarks). Cover is skipped. Default false."
            ),
            "favorites": _bool(
                "Optional Hobonichi-style Favorites page. `true` → one page. "
                "Default off. Prefer this bool over `favorites_pages`."
            ),
            "favorites_pages": _int_range(
                0,
                1,
                "Favorites page count. 0 off, 1 on. Prefer `favorites = true`.",
            ),
            "my_100": _bool("Optional My 100 year list. Default false."),
            "checkoff_365": _bool(
                "Optional 365-day check-off sheet. Default false. "
                "Dest id keeps `365` as the product name."
            ),
            "notes_pages": _int_range(
                0,
                32,
                "Leftover top-level notes well count. Prefer `[daily] notes_pages`.",
            ),
            "habit_columns": _int_range(
                4, 16, "Leftover habit grid columns. Prefer `[habits] columns`."
            ),
            "habit_rows": _int_range(
                4,
                16,
                "Leftover alias for habit columns. Prefer `[habits] columns`.",
            ),
            "priority_rows": _int_range(
                4, 8, "Leftover daily priority rows. Prefer `[daily] priority_rows`."
            ),
            "project_cards": _int_range(
                2, 4, "Leftover project cards. Prefer `[projects] cards`."
            ),
            "project_tickets": _int_range(
                6, 10, "Leftover tickets per index page. Prefer `[projects] tickets`."
            ),
            "project_index_pages": _int_range(
                1, 6, "Leftover projects index pages. Prefer `[projects] index_pages`."
            ),
            "meeting_index_rows": _int_range(
                12, 20, "Leftover meeting roster rows. Prefer `[meetings] index_rows`."
            ),
            "task_rows": _int_range(
                4, 8, "Leftover weekly task rows (TOML floor). Prefer `[tasks] rows`."
            ),
            "engineering_sheets": _int_range(
                0,
                100,
                "Leftover duplex eng-pad sheets. Prefer `[engineering] sheets`. "
                "Cannot combine with `[steno] sheets`.",
            ),
            "steno_sheets": _int_range(
                0,
                100,
                "Leftover single-face Gregg sheets. Prefer `[steno] sheets`. "
                "Cannot combine with `[engineering] sheets`.",
            ),
            "daily": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "schedule": schedule,
                    "notes_pages": _int_range(
                        0,
                        32,
                        "Daily notes wells per day. 0 skips notes dests. Default 2 "
                        "(examples often use 1).",
                    ),
                    "priority_rows": _int_range(
                        4, 8, "Daily priority lines. Default 6. Closed band 4–8."
                    ),
                },
                **_md("Daily page knobs: schedule window, notes wells, priority rows."),
            },
            "daily_notes": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "pages": _int_range(
                        0,
                        32,
                        "Leftover notes well count. Prefer `[daily] notes_pages`.",
                    ),
                },
                **_md("Leftover notes table. Prefer `[daily] notes_pages`."),
            },
            "habits": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "columns": _int_range(
                        4, 16, "Habit tracker columns. Sealed default 10. Closed 4–16."
                    ),
                    "rows": _int_range(
                        4,
                        16,
                        "Alias for `columns` (older spelling). Prefer `columns`.",
                    ),
                },
                **_md("Monthly habit grid. Prefer `columns` over leftover `rows`."),
            },
            "projects": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "cards": _int_range(
                        2, 4, "Index card / preview count. Default 3. Closed 2–4."
                    ),
                    "tickets": _int_range(
                        6,
                        10,
                        "Rows per index page (one row → one projects dest). "
                        "Default 8. Closed 6–10.",
                    ),
                    "tickets_per_page": _int_range(
                        6, 10, "Alias for `tickets`. Prefer `tickets`."
                    ),
                    "index_pages": _int_range(
                        1,
                        6,
                        "Projects index pages. Default 1. "
                        "`project_count = index_pages × tickets`.",
                    ),
                },
                **_md(
                    "Projects index + dest pages. `tasks` inside this table is "
                    "ignored leftover — do not set it."
                ),
            },
            "meetings": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "index_rows": _int_range(
                        12,
                        20,
                        "Dated roster rows (one row → one meeting dest). "
                        "Default 16. Closed 12–20.",
                    ),
                },
                **_md("Meetings index roster."),
            },
            "tasks": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "rows": _int_range(
                        4,
                        8,
                        "Weekly Tasks row floor; dest paint may fit more. "
                        "Default 6. Closed 4–8.",
                    ),
                },
                **_md("Weekly Tasks dest knobs."),
            },
            "engineering": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "sheets": _int_range(
                        0,
                        100,
                        "Duplex fronts+backs. 0 keeps year-planner press. "
                        '`book = "engineering-notebook"` requires >= 1.',
                    ),
                },
                **_md(
                    "Engineering / computation pad. Mutually exclusive with `[steno]`."
                ),
            },
            "steno": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "sheets": _int_range(
                        0,
                        100,
                        "Single-face Gregg pages. 0 keeps year-planner press. "
                        "No steno-notebook book yet.",
                    ),
                },
                **_md("Gregg steno pad. Mutually exclusive with `[engineering]`."),
            },
            "bujo": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "index_pages": _int_range(
                        1, 6, "Bullet-journal index pages. Default 2. Closed 1–6."
                    ),
                    "collections": _int_range(
                        0, 48, "Collection dests. Default 24. Closed 0–48."
                    ),
                },
                **_md(
                    '`[bujo]` for `book = "bullet-journal"`. Unknown keys fail loudly.'
                ),
            },
            "typography": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "overlay": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["schema_version"],
                        "properties": _overlay_properties(),
                        **_md(
                            "Closed TypeStep → TypePatch table. Unknown steps "
                            "(old roles like `cover_year`) fail before paint. "
                            f"`schema_version` must be {OVERLAY_SCHEMA_VERSION}."
                        ),
                    },
                },
                **_md(
                    "Typography knobs. Only `overlay` is accepted; `family` "
                    "and other keys fail loudly. Omit the table for closed "
                    "Jost defaults."
                ),
            },
        },
    }


def dump_schema(*, indent: int = 2) -> str:
    """Pretty-printed JSON Schema with a trailing newline."""
    return json.dumps(spec_schema(), indent=indent, ensure_ascii=False) + "\n"


def write_schema(path: Path) -> Path:
    """Write schema JSON. A directory (or suffix-less path) gets ``spec.schema.json``."""
    dest = path / SCHEMA_FILENAME if path.is_dir() or path.suffix == "" else path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(dump_schema(), encoding="utf-8")
    return dest


def init_toml() -> str:
    """Tiny starter Spec. Schema comments first so Taplo sees a header directive."""
    return (
        f"{SCHEMA_DIRECTIVE}\n"
        f"{SCHEMA_COMMENT}\n"
        "\n"
        "year = 2026\n"
        'device = "supernote-nomad"\n'
        'week_start = "monday"\n'
        "months = { from = 1, to = 12 }\n"
        'title = "Year planner"\n'
    )


def _init_paths(target: Path) -> tuple[Path, Path]:
    """``(toml_path, schema_path)`` for ``parch init``."""
    if target.exists() and target.is_dir():
        toml_path = target / DEFAULT_INIT_NAME
    elif target.suffix.lower() == ".toml":
        toml_path = target
    else:
        toml_path = target / DEFAULT_INIT_NAME
    return toml_path, toml_path.parent / SCHEMA_FILENAME


def write_init(target: Path, *, force: bool = False) -> tuple[Path, Path]:
    """Write starter TOML + sibling schema. Refuse overwrites unless ``force``."""
    toml_path, schema_path = _init_paths(target)
    if not force:
        existing = [p for p in (toml_path, schema_path) if p.exists()]
        if existing:
            names = ", ".join(str(p) for p in existing)
            raise ConfigError(f"refusing to overwrite {names} (pass --force)")
    toml_path.parent.mkdir(parents=True, exist_ok=True)
    toml_path.write_text(init_toml(), encoding="utf-8")
    write_schema(schema_path)
    return toml_path, schema_path


def _schema_cmd(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="parch schema",
        description="Dump the JSON Schema for Spec TOML (editor autocomplete / key docs).",
    )
    parser.add_argument(
        "-o",
        "--output",
        help=f"Write schema JSON here (default: stdout). Directories get {SCHEMA_FILENAME}.",
    )
    args = parser.parse_args(argv)
    text = dump_schema()
    if args.output:
        dest = write_schema(Path(args.output))
        print(dest)
        return 0
    sys.stdout.write(text)
    return 0


def _init_cmd(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="parch init",
        description=(
            f"Write a tiny Spec TOML with `{SCHEMA_COMMENT}` and a sibling "
            f"{SCHEMA_FILENAME} so editors can autocomplete keys."
        ),
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=DEFAULT_INIT_NAME,
        help=f"TOML file or directory (default: {DEFAULT_INIT_NAME}).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing starter / schema file.",
    )
    args = parser.parse_args(argv)
    try:
        toml_path, schema_path = write_init(Path(args.path), force=args.force)
    except ConfigError as exc:
        print(f"parch: {exc}", file=sys.stderr)
        return 2
    print(toml_path)
    print(schema_path)
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry. ``argv[0]`` is ``schema`` or ``init`` (the verb)."""
    raw = list(sys.argv[1:] if argv is None else argv)
    if not raw:
        print("parch: expected schema or init", file=sys.stderr)
        return 2
    verb, rest = raw[0], raw[1:]
    if verb == "schema":
        return _schema_cmd(rest)
    if verb == "init":
        return _init_cmd(rest)
    print(f"parch: unknown schema verb {verb!r}", file=sys.stderr)
    return 2
