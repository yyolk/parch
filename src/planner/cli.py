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
    args = parser.parse_args(argv)
    out = Path(args.output) if args.output else Path("artifacts") / f"planner-{args.year}.pdf"
    if args.specimen and args.output is None:
        out = Path("artifacts") / f"specimen-{args.year}.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    write_pdf(str(out), year=args.year, specimen=args.specimen)
    print(out.resolve())
    return 0
