#!/usr/bin/env python3
"""Raster specimen PDF pages to artifacts/preview/*.png via pdftoppm."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "artifacts" / "specimen-2026.pdf"
OUT = ROOT / "artifacts" / "preview"
NAMES = ("cover", "year", "quarter", "month", "week", "day")


def main() -> int:
    if not PDF.is_file():
        print(f"missing {PDF}", file=sys.stderr)
        return 1
    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        print("pdftoppm not on PATH (install poppler-utils)", file=sys.stderr)
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    prefix = OUT / "page"
    subprocess.run(
        [pdftoppm, "-png", "-r", "140", str(PDF), str(prefix)],
        check=True,
    )
    for i, name in enumerate(NAMES, start=1):
        src = OUT / f"page-{i}.png"
        if not src.is_file():
            src = OUT / f"page-{i:02d}.png"
        if not src.is_file():
            print(f"missing raster for page {i}", file=sys.stderr)
            return 1
        dest = OUT / f"{name}.png"
        src.replace(dest)
        print(dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
