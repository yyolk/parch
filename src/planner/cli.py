"""press — write a yearly planner PDF."""

from __future__ import annotations

import argparse
from pathlib import Path

from planner.book import write_pdf


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="press",
        description="Generate a minimal yearly planner PDF (fpdf2 greenfield spike).",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2026,
        help="Calendar year (default: 2026).",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output PDF path (default: artifacts/planner-YEAR.pdf).",
    )
    parser.add_argument(
        "--specimen",
        action="store_true",
        help="Cover + year + Q1 + January + first week + 1 January only.",
    )
    parser.add_argument(
        "--notes-pages",
        type=int,
        default=0,
        metavar="N",
        help=(
            "Dedicated lined notes pages after each day page. "
            "N=0 (default): day page only, with its on-page notes panel. "
            "N=2: day + 2 notes pages. N=20: day + 20 notes pages."
        ),
    )
    args = parser.parse_args(argv)
    if args.notes_pages < 0:
        parser.error("--notes-pages must be >= 0")
    if args.output:
        out = Path(args.output)
    elif args.specimen:
        suffix = f"-notes{args.notes_pages}" if args.notes_pages else ""
        out = Path("artifacts") / f"specimen-{args.year}{suffix}.pdf"
    else:
        suffix = f"-notes{args.notes_pages}" if args.notes_pages else ""
        out = Path("artifacts") / f"planner-{args.year}{suffix}.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    write_pdf(str(out), year=args.year, specimen=args.specimen, notes_pages=args.notes_pages)
    print(out.resolve())
    return 0
