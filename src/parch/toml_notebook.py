"""Progressive TOML notebook — tiny init, comment accretion on present keys.

``parch init`` writes year + device (and a book table only when required).
``parch doctor`` / ``parch explain`` / ``parch init --annotate`` insert or
refresh ``# parch:`` lines for keys the file already has. User values and
user comments stay put. No questionary; no schema dump of unused keys.
"""

import argparse
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

from parch import ConfigError
from parch.devices import get_device, known_device_ids
from parch.fonts.ramp import TYPE_STEPS
from parch.spec import Spec

DEFAULT_SPEC = Path("parch.toml")
MANAGED_PREFIX = "# parch:"

_TABLE = re.compile(r"^(\s*)\[\[?([A-Za-z0-9_.-]+)\]\]?\s*(?:#.*)?$")
_KEY = re.compile(r"^(\s*)([A-Za-z0-9_.-]+)\s*=")
_MANAGED = re.compile(r"^(\s*)#\s*parch:\s*(.*)$")

_BOOKS = (
    "year-planner",
    "projects-notebook",
    "engineering-notebook",
    "bullet-journal",
)


def _key_docs() -> dict[str, str]:
    """Closed catalog: dotted path → one-line comment. Only present keys get these."""
    docs: dict[str, str] = {
        "year": "calendar year the book is pressed for. Default 2026.",
        "device": (
            "slate id: supernote-nomad or kindle-scribe "
            "(aliases nomad, scribe). Default supernote-nomad."
        ),
        "week_start": "first weekday of the week grid: monday or sunday. Default monday.",
        "months": (
            "pressed months. List of ints, { from, to } closed table, "
            "or omit for the full year."
        ),
        "months.from": "inclusive first calendar month (1–12) of a { from, to } span.",
        "months.to": "inclusive last calendar month (1–12) of a { from, to } span.",
        "month": "singleton month (1–12). Shorthand for a one-month press.",
        "title": "cover brow / sibling headline. Omit keeps paint's house title.",
        "book": (
            "year-planner, projects-notebook, engineering-notebook, "
            "or bullet-journal. Default year-planner."
        ),
        "outline": "reader sidebar outline (bookmarks). Cover is skipped. Default false.",
        "notes_pages": "daily notes wells per day. Prefer [daily] notes_pages. Default 2.",
        "habit_columns": "habit grid columns (4–16). Prefer [habits] columns. Default 10.",
        "habit_rows": "legacy alias for habit_columns. Prefer [habits] columns.",
        "priority_rows": "daily priority lines (4–8). Prefer [daily] priority_rows. Default 6.",
        "project_cards": "project cards per dest page (2–4). Prefer [projects] cards. Default 3.",
        "project_tickets": (
            "index rows per projects index page (6–10). "
            "Prefer [projects] tickets. Default 8."
        ),
        "project_index_pages": (
            "projects index page count (1–6). Prefer [projects] index_pages. Default 1."
        ),
        "meeting_index_rows": (
            "meetings roster rows (12–20). Prefer [meetings] index_rows. Default 16."
        ),
        "task_rows": "weekly task lines (4–8). Prefer [tasks] rows. Default 6.",
        "engineering_sheets": (
            "duplex pad sheet count (0–100). Prefer [engineering] sheets. "
            "0 keeps year-planner press."
        ),
        "steno_sheets": (
            "single-face Gregg pages (0–100). Prefer [steno] sheets. "
            "0 keeps year-planner press."
        ),
        "favorites": "Hobonichi-style rankings page. true → one favorites sheet.",
        "favorites_pages": "favorites sheet count (0–1). 0 keeps year-planner press.",
        "my_100": "optional My 100 list. Default false.",
        "checkoff_365": "optional year check-off sheet. Default false.",
        "daily": "daily well — schedule hour labels, notes pages, priority rows.",
        "daily.schedule": (
            "local-time { from, to } via tomlrange Clock. "
            "Optional step is Clock grain (minutes). Default 07:00–16:00."
        ),
        "daily.schedule.from": "inclusive start of the daily well (naive local time).",
        "daily.schedule.to": "inclusive end of the daily well (naive local time).",
        "daily.schedule.step": (
            "Clock grain: positive int minutes, or a time as length-since-midnight."
        ),
        "daily.notes_pages": "notes wells after each daily page. Default 2.",
        "daily.priority_rows": "priority lines on the daily page (4–8). Default 6.",
        "daily_notes": "legacy notes table. Prefer [daily] notes_pages.",
        "daily_notes.pages": "legacy notes well count. Prefer [daily] notes_pages.",
        "habits": "habit tracker columns for each pressed month.",
        "habits.columns": "habit grid columns (4–16). Default 10.",
        "habits.rows": "legacy alias for habits.columns.",
        "projects": "projects index + dest pages (year-planner or projects-notebook).",
        "projects.cards": "cards on each project dest page (2–4). Default 3.",
        "projects.tickets": "index rows per projects index page (6–10). Default 8.",
        "projects.tickets_per_page": "alias for projects.tickets.",
        "projects.index_pages": "projects index page count (1–6). Default 1.",
        "meetings": "meetings roster + dest notes pages.",
        "meetings.index_rows": "roster rows (12–20); one dest page each. Default 16.",
        "tasks": "weekly tasks index + dest pages.",
        "tasks.rows": "task lines on each weekly dest (4–8). Default 6.",
        "engineering": "duplex engineering / computation pad. Required when book is engineering-notebook.",
        "engineering.sheets": (
            "duplex fronts+backs (1–100 for engineering-notebook; 0 keeps year-planner)."
        ),
        "steno": "single-face Gregg stenographer pad (no steno-notebook book yet).",
        "steno.sheets": "Gregg pages (1–100 to press the pad alone; 0 keeps year-planner).",
        "bujo": "bullet-journal index + collections. Unknown keys fail loudly.",
        "bujo.index_pages": "bujo index page count (1–6). Default 2.",
        "bujo.collections": "collection dest pages (0–48). Default 24.",
        "typography": "optional type overlay table. Unknown keys fail loudly.",
        "typography.overlay": (
            "closed TypeStep patches. schema_version must match exactly. "
            "Size is an absolute Pt override; it does not rescale siblings."
        ),
        "typography.overlay.schema_version": (
            "exact overlay schema match (1 today). Missing or mismatched fails press."
        ),
    }
    for step in TYPE_STEPS:
        docs[f"typography.overlay.{step}"] = (
            f"absolute Pt / Jost weight patch for the {step} step. "
            "Does not rescale siblings."
        )
        docs[f"typography.overlay.{step}.size"] = (
            f"absolute Pt override for {step}. Inclusive closed band per step."
        )
        docs[f"typography.overlay.{step}.weight"] = (
            f"Jost cut for {step}: book, medium, bold, or heavy."
        )
    return docs


KEY_DOCS = _key_docs()


@dataclass(frozen=True, slots=True)
class KeyHit:
    """One table header or assignment, with 0-based line index."""

    path: str
    line: int
    indent: str


def present_paths(text: str) -> tuple[str, ...]:
    """Dotted paths of table headers and assignments, file order, first seen."""
    seen: list[str] = []
    for hit in _hits(text.splitlines()):
        if hit.path not in seen:
            seen.append(hit.path)
    return tuple(seen)


def documented_paths(text: str) -> tuple[str, ...]:
    """Present paths that have a catalog comment (used or unused)."""
    return tuple(path for path in present_paths(text) if path in KEY_DOCS)


def unknown_paths(text: str) -> tuple[str, ...]:
    """Present paths with no catalog entry — leftovers Spec may ignore."""
    return tuple(path for path in present_paths(text) if path not in KEY_DOCS)


def annotate(text: str) -> str:
    """Insert or refresh ``# parch:`` comments for present catalog keys.

    User comments and every assignment stay. A managed line is refreshed
    in place; a missing one is inserted immediately above the key (after
    any user comments in the adjacent block). Idempotent.
    """
    lines = text.splitlines()
    hits = [hit for hit in _hits(lines) if hit.path in KEY_DOCS]
    for hit in reversed(hits):
        managed = f"{hit.indent}{MANAGED_PREFIX} {KEY_DOCS[hit.path]}"
        block_start = hit.line
        cursor = hit.line - 1
        while cursor >= 0 and lines[cursor].lstrip().startswith("#"):
            cursor -= 1
        block_start = cursor + 1
        managed_at: int | None = None
        for index in range(block_start, hit.line):
            if _MANAGED.match(lines[index]):
                managed_at = index
                break
        if managed_at is not None:
            if lines[managed_at] != managed:
                lines[managed_at] = managed
        else:
            lines.insert(hit.line, managed)
    if not lines:
        return text
    return "\n".join(lines) + "\n"


def explain_text(text: str) -> str:
    """Stdout notebook: present catalog keys and their comments, file order."""
    chunks: list[str] = []
    for path in documented_paths(text):
        chunks.append(f"{path}\n  {KEY_DOCS[path]}")
    leftover = unknown_paths(text)
    if leftover:
        chunks.append("undocumented keys: " + ", ".join(leftover))
    return "\n\n".join(chunks) + ("\n" if chunks else "")


def minimal_toml(
    *,
    year: int = 2026,
    device: str = "supernote-nomad",
    book: str | None = None,
) -> str:
    """Tiny pressable starter. No unused keys, no comment dump."""
    get_device(device)
    lines = [f"year = {year}", f'device = "{device}"']
    kind = book or "year-planner"
    if kind != "year-planner":
        if kind not in _BOOKS:
            raise ConfigError(
                "book must be year-planner, projects-notebook, "
                f"engineering-notebook, or bullet-journal, not {kind!r}"
            )
        lines.append(f'book = "{kind}"')
        if kind == "engineering-notebook":
            lines.append("")
            lines.append("[engineering]")
            lines.append("sheets = 1")
    return "\n".join(lines) + "\n"


def write_init(
    path: Path,
    *,
    year: int = 2026,
    device: str = "supernote-nomad",
    book: str | None = None,
    annotate_keys: bool = False,
    force: bool = False,
) -> Path:
    """Write a minimal spec. Refuse an existing path unless ``force``."""
    if path.exists() and not force:
        raise ConfigError(f"refusing to overwrite {path}; pass --force")
    text = minimal_toml(year=year, device=device, book=book)
    if annotate_keys:
        text = annotate(text)
    Spec.from_mapping(tomllib.loads(text))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def annotate_path(path: Path) -> tuple[str, bool]:
    """Annotate ``path`` in place. Returns ``(text, changed)``."""
    raw = path.read_text(encoding="utf-8")
    try:
        tomllib.loads(raw)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"invalid TOML {path}: {exc}") from exc
    written = annotate(raw)
    changed = written != raw
    if changed:
        path.write_text(written, encoding="utf-8")
    return written, changed


def _hits(lines: list[str]) -> list[KeyHit]:
    hits: list[KeyHit] = []
    table = ""
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        table_match = _TABLE.match(line)
        if table_match:
            table = table_match.group(2)
            hits.append(KeyHit(table, index, table_match.group(1)))
            continue
        key_match = _KEY.match(line)
        if key_match:
            name = key_match.group(2)
            path = f"{table}.{name}" if table else name
            hits.append(KeyHit(path, index, key_match.group(1)))
    return hits


def _spec_path(token: str | None) -> Path:
    path = Path(token) if token else DEFAULT_SPEC
    if not path.is_file():
        raise ConfigError(f"spec file not found: {path}")
    return path


def _report_annotation(path: Path, text: str, changed: bool) -> None:
    keys = documented_paths(text)
    verb = "annotated" if changed else "already documented"
    print(f"{verb} {path} ({len(keys)} keys)")
    leftover = unknown_paths(text)
    if leftover:
        print(f"undocumented keys: {', '.join(leftover)}")


def _load_after(path: Path) -> Spec:
    return Spec.from_path(path)


def init_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="parch init",
        description="Write a tiny press spec. Add keys yourself; doctor documents them.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=str(DEFAULT_SPEC),
        help="TOML path (default parch.toml).",
    )
    parser.add_argument("--year", type=int, default=2026, help="Planner year.")
    parser.add_argument(
        "--device",
        default="supernote-nomad",
        help=(
            "Device id (default supernote-nomad). "
            f"Known: {', '.join(known_device_ids())}."
        ),
    )
    parser.add_argument(
        "--book",
        default=None,
        help="Book kind. Omit for year-planner defaults (no book key).",
    )
    parser.add_argument(
        "--annotate",
        action="store_true",
        help="Write # parch: comments for the keys this file actually has.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing file.",
    )
    args = parser.parse_args(argv)
    try:
        path = write_init(
            Path(args.output),
            year=args.year,
            device=args.device,
            book=args.book,
            annotate_keys=args.annotate,
            force=args.force,
        )
    except ConfigError as exc:
        print(f"parch: {exc}", file=sys.stderr)
        return 2
    print(path)
    return 0


def doctor_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="parch doctor",
        description="Validate a spec and accrete # parch: comments on keys already present.",
    )
    parser.add_argument(
        "spec",
        nargs="?",
        default=None,
        help="TOML spec path (default parch.toml).",
    )
    args = parser.parse_args(argv)
    try:
        path = _spec_path(args.spec)
        text, changed = annotate_path(path)
        _report_annotation(path, text, changed)
        spec = _load_after(path)
    except ConfigError as exc:
        print(f"parch: {exc}", file=sys.stderr)
        return 2
    print(f"ok: {spec.book} {spec.year} {spec.device}")
    return 0


def explain_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="parch explain",
        description="Print docs for keys the file already has; accrete the same # comments.",
    )
    parser.add_argument(
        "spec",
        nargs="?",
        default=None,
        help="TOML spec path (default parch.toml).",
    )
    args = parser.parse_args(argv)
    try:
        path = _spec_path(args.spec)
        text, changed = annotate_path(path)
        _report_annotation(path, text, changed)
        body = explain_text(text)
        if body:
            print(body, end="")
        spec = _load_after(path)
    except ConfigError as exc:
        print(f"parch: {exc}", file=sys.stderr)
        return 2
    print(f"ok: {spec.book} {spec.year} {spec.device}")
    return 0


def notebook_verb(name: str, argv: list[str]) -> int:
    """Dispatch init / doctor / explain. Unknown name is a programming error."""
    match name:
        case "init":
            return init_main(argv)
        case "doctor":
            return doctor_main(argv)
        case "explain":
            return explain_main(argv)
        case _:
            raise ValueError(f"unknown notebook verb {name!r}")
