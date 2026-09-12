"""One-off Kindle Scribe OS-band probe. Not a product page.

Press:
    uv run python scripts/scribe_band_probe.py -o out/scribe-band-probe.pdf

Send-to-Kindle the PDF. Finger-tap (not pen). Each box is a real named
dest link whose centre sits N mm above the glass bottom. Confirm pages
say HIT N mm. Mid-page control should always work.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from parch.devices import SCRIBE
from parch.fonts.ramp import TypeRef
from parch.geom import Rect
from parch.plotter.fpdf2 import Fpdf2Plotter

# mm above the glass bottom. 6.35 is Templacity visual chrome; 8/16 are #334.
TARGETS = (2, 4, 6, 8, 10, 12, 16, 20)
MARKS = (6.35, 8.0, 16.0)
BOX_H = 3.2
INK = 0.0
MUTED = 112 / 255
WASH = 236 / 255
SOFT = 210 / 255


def _dest(mm: float) -> str:
    return f"hit-{mm:g}mm".replace(".", "p")


def paint_probe(plotter: Fpdf2Plotter) -> None:
    d = plotter.device
    plotter.begin_page()
    plotter.add_dest("probe")

    plotter.rect(
        Rect(0.0, d.page_height - 16.0, d.page_width, 16.0),
        stroke=False,
        fill=True,
        fill_gray=WASH,
    )
    plotter.line(0.0, d.page_height - 8.0, d.page_width, d.page_height - 8.0, stroke_width=0.18, stroke_gray=SOFT)
    plotter.line(0.0, d.page_height - 16.0, d.page_width, d.page_height - 16.0, stroke_width=0.18, stroke_gray=INK)

    plotter.text(
        Rect(6.0, 8.0, d.page_width - 12.0, 8.0),
        "Scribe OS band probe",
        ref=TypeRef(step="title"),
        gray=INK,
    )
    plotter.text(
        Rect(6.0, 16.5, d.page_width - 12.0, 6.0),
        f"{d.page_width:g} x {d.page_height:g} mm   1860x2480 @ 300 PPI",
        ref=TypeRef(step="caption"),
        gray=MUTED,
    )
    plotter.text(
        Rect(6.0, 23.0, d.page_width - 12.0, 14.0),
        "Finger tap each box. Link works = that height is above the OS band."
        " Page-turn / chrome / no jump = still inside the dead zone.",
        ref=TypeRef(step="body"),
        gray=INK,
    )
    plotter.text(
        Rect(6.0, 38.0, d.page_width - 12.0, 6.0),
        "#334 wash 0-16 mm   hits 8-16 mm   Templacity visual 6.35 mm",
        ref=TypeRef(step="caption"),
        gray=MUTED,
    )

    mid = Rect(18.0, 52.0, d.page_width - 36.0, 12.0)
    plotter.rect(mid, stroke=True, fill=True, stroke_width=0.22, fill_gray=WASH, stroke_gray=INK)
    plotter.text(mid, "CONTROL  mid-page  ~100 mm from bottom", ref=TypeRef(step="chrome"), gray=INK, align="center", small_caps=True)
    plotter.link(mid, "hit-mid")

    # 1 mm ticks along the right edge for 0-24 mm from the bottom.
    ruler_x = d.page_width - 14.0
    for mm in range(0, 25):
        y = d.page_height - mm
        tick = 4.0 if mm % 4 == 0 else 2.2
        plotter.line(ruler_x, y, ruler_x + tick, y, stroke_width=0.12 if mm % 2 else 0.18, stroke_gray=INK)
        if mm % 4 == 0:
            plotter.text(
                Rect(ruler_x - 14.0, y - 2.2, 13.0, 4.4),
                f"{mm}",
                ref=TypeRef(step="micro"),
                gray=INK,
                align="right",
            )

    slot = (d.page_width - 28.0) / len(TARGETS)
    for i, mm in enumerate(TARGETS):
        y = d.page_height - mm - BOX_H / 2.0
        box = Rect(6.0 + i * slot, y, slot - 1.4, BOX_H)
        plotter.rect(box, stroke=True, fill=True, stroke_width=0.18, fill_gray=1.0, stroke_gray=INK)
        plotter.text(box, f"{mm:g}", ref=TypeRef(step="label", emphasis="strong"), gray=INK, align="center")
        plotter.link(box, _dest(mm))

    plotter.text(
        Rect(6.0, d.page_height - 28.0, 90.0, 5.0),
        "boxes centred on N mm from glass",
        ref=TypeRef(step="micro"),
        gray=MUTED,
    )


def paint_hit(plotter: Fpdf2Plotter, label: str, dest: str) -> None:
    d = plotter.device
    plotter.begin_page()
    plotter.add_dest(dest)
    plotter.text(
        Rect(8.0, 70.0, d.page_width - 16.0, 16.0),
        label,
        ref=TypeRef(step="display"),
        gray=INK,
        align="center",
    )
    back = Rect(28.0, 100.0, d.page_width - 56.0, 12.0)
    plotter.rect(back, stroke=True, fill=False, stroke_width=0.22, stroke_gray=INK)
    plotter.text(back, "back to probe", ref=TypeRef(step="chrome"), gray=INK, align="center", small_caps=True)
    plotter.link(back, "probe")


def press_probe(output: Path) -> Path:
    plotter = Fpdf2Plotter(SCRIBE)
    plotter.reserve_dest("probe")
    plotter.reserve_dest("hit-mid")
    for mm in TARGETS:
        plotter.reserve_dest(_dest(mm))
    paint_probe(plotter)
    paint_hit(plotter, "HIT mid-page", "hit-mid")
    for mm in TARGETS:
        paint_hit(plotter, f"HIT {mm:g} mm", _dest(mm))
    plotter.finish(output)
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="scribe-band-probe")
    parser.add_argument("-o", "--output", default="out/scribe-band-probe.pdf")
    args = parser.parse_args(argv)
    path = press_probe(Path(args.output))
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
