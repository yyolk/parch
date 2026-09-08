"""CLI: `press` and `python -m planner`."""

from __future__ import annotations

import argparse
from pathlib import Path

from planner.emit import write_pdf


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="press",
        description="Write a 106 × 144 mm Monday-week yearly planner (fpdf2 spike v2).",
    )
    p.add_argument("--year", type=int, default=2026, help="Planner year (default 2026).")
    p.add_argument(
        "--notes-pages",
        type=int,
        default=0,
        metavar="N",
        help="Dedicated notes pages per day (default 0: notes on the day page only).",
    )
    p.add_argument(
        "--specimen",
        action="store_true",
        help="Cover + year + Q1 + January + first week + 1 Jan (plus that day's notes).",
    )
    p.add_argument("-o", "--output", type=Path, default=None, help="Output PDF path.")
    return p


def default_output(year: int, notes_pages: int, specimen: bool) -> Path:
    if specimen:
        if notes_pages:
            return Path(f"artifacts/specimen-{year}-notes{notes_pages}.pdf")
        return Path(f"artifacts/specimen-{year}.pdf")
    if notes_pages:
        return Path(f"artifacts/planner-{year}-notes{notes_pages}.pdf")
    return Path(f"artifacts/planner-{year}.pdf")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.notes_pages < 0:
        raise SystemExit("--notes-pages must be >= 0")
    out = args.output or default_output(args.year, args.notes_pages, args.specimen)
    path = write_pdf(out, year=args.year, notes_pages=args.notes_pages, specimen=args.specimen)
    print(path)
    return 0
