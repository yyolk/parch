#!/usr/bin/env python3
"""Raster specimen landings with pdftoppm (150 dpi)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "artifacts" / "specimen-2026.pdf"
OUT = ROOT / "artifacts" / "preview"
NAMES = ("cover", "year", "quarter", "month", "week", "day")


def main() -> int:
    pdf = Path(sys.argv[1]) if len(sys.argv) > 1 else PDF
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else OUT
    out.mkdir(parents=True, exist_ok=True)
    tmp = out / "_ppm"
    subprocess.run(
        ["pdftoppm", "-png", "-r", "150", str(pdf), str(tmp)],
        check=True,
    )
    pages = sorted(out.glob("_ppm-*.png"))
    for name, src in zip(NAMES, pages):
        dest = out / f"{name}.png"
        dest.write_bytes(src.read_bytes())
        src.unlink()
    extra = list(out.glob("_ppm-*.png"))
    if extra:
        # notes pages after day when specimen --notes-pages N
        for i, src in enumerate(extra, start=1):
            dest = out / f"day-notes{i}.png"
            dest.write_bytes(src.read_bytes())
            src.unlink()
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
