"""CLI: press [--year] [--notes-pages N] [--specimen] [-o PATH]."""

from __future__ import annotations

import argparse
from pathlib import Path

from planner.press import write_planner


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="press",
        description="ReportLab yearly planner spike (DO NOT MERGE).",
    )
    p.add_argument("--year", type=int, default=2026, help="Planner year (default 2026)")
    p.add_argument(
        "--notes-pages",
        type=int,
        default=0,
        metavar="N",
        help="Dedicated lined notes pages per day (default 0 = day page only)",
    )
    p.add_argument(
        "--specimen",
        action="store_true",
        help="Cover + year + Q1 + January + first week + 1 Jan (+ notes if N>0)",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output PDF path",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.notes_pages < 0:
        raise SystemExit("--notes-pages must be >= 0")
    if args.output is None:
        stem = "specimen" if args.specimen else "planner"
        extra = f"-notes{args.notes_pages}" if args.notes_pages else ""
        args.output = Path("artifacts") / f"{stem}-{args.year}{extra}.pdf"
    path = write_planner(
        year=args.year,
        notes_pages=args.notes_pages,
        specimen=args.specimen,
        output=args.output,
    )
    print(path)
    return 0
