"""Kindle Scribe side-depth probe. Walk inward until a PDF link wins.

Press:
    uv run python scripts/scribe_side_depth_probe.py -o out/scribe-side-depth-probe.pdf

Prior result: 2–32 mm from left/right glass all page-turn on Send-to-Kindle
(≤20 mm BACK, 24/32 mm FORWARD). Mid-page CONTROL still works. This file
starts at 32 mm and steps to 80 mm (~page centre) to find the first live
side tap. Finger or stylus hand-tool. Confirm pages say HIT LEFT/RIGHT N mm.

Fpdf2Plotter is top-left millimetres: y=0 is the top glass edge.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from parch.devices import SCRIBE
from parch.fonts.ramp import TypeRef
from parch.geom import Rect
from parch.plotter.fpdf2 import Fpdf2Plotter

# 32 already died. 80 mm is just past centre of 157.48 mm.
SIDE_TARGETS = (32, 40, 48, 56, 64, 72, 80)
BOX = 3.2
SIDE_H = 14.0
SIDE_GAP = 5.0
INK = 0.0
MUTED = 112 / 255
WASH = 236 / 255


def _dest(edge: str, mm: float) -> str:
    return f"hit-{edge}-{mm:g}mm".replace(".", "p")


def _mid(edge: str) -> str:
    return f"hit-{edge}-mid"


def _control(plotter: Fpdf2Plotter, box: Rect, dest: str, caption: str) -> None:
    plotter.rect(box, stroke=True, fill=True, stroke_width=0.22, fill_gray=WASH, stroke_gray=INK)
    plotter.text(
        box,
        caption,
        ref=TypeRef(step="chrome"),
        gray=INK,
        align="center",
        small_caps=True,
    )
    plotter.link(box, dest)


def _back(plotter: Fpdf2Plotter, dest: str, label: str) -> None:
    d = plotter.device
    box = Rect(28.0, 100.0, d.page_width - 56.0, 12.0)
    plotter.rect(box, stroke=True, fill=False, stroke_width=0.22, stroke_gray=INK)
    plotter.text(box, label, ref=TypeRef(step="chrome"), gray=INK, align="center", small_caps=True)
    plotter.link(box, dest)


def paint_hit(plotter: Fpdf2Plotter, label: str, dest: str, back_dest: str, back_label: str) -> None:
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
    _back(plotter, back_dest, back_label)


def paint_index(plotter: Fpdf2Plotter) -> None:
    d = plotter.device
    plotter.begin_page()
    plotter.add_dest("index")
    plotter.text(
        Rect(8.0, 8.0, d.page_width - 16.0, 10.0),
        "Scribe side depth probe",
        ref=TypeRef(step="title"),
        gray=INK,
    )
    plotter.text(
        Rect(8.0, 18.5, d.page_width - 16.0, 6.0),
        f"{d.page_width:g} x {d.page_height:g} mm   2-32 mm already page-turned",
        ref=TypeRef(step="caption"),
        gray=MUTED,
    )
    plotter.text(
        Rect(8.0, 26.0, d.page_width - 16.0, 16.0),
        "Send-to-Kindle. Finger or stylus hand-tool. HIT page = that offset "
        "from the named edge is usable. Page-turn = EasyReach still owns it. "
        "CONTROL must work or the file is the problem.",
        ref=TypeRef(step="body"),
        gray=INK,
    )

    nav = (
        ("LEFT  32-80 mm", "probe-left"),
        ("RIGHT  32-80 mm", "probe-right"),
    )
    y0 = 52.0
    for i, (label, dest) in enumerate(nav):
        box = Rect(18.0, y0 + i * 16.0, d.page_width - 36.0, 12.0)
        plotter.rect(box, stroke=True, fill=True, stroke_width=0.22, fill_gray=WASH, stroke_gray=INK)
        plotter.text(box, label, ref=TypeRef(step="chrome"), gray=INK, align="center", small_caps=True)
        plotter.link(box, dest)

    _control(
        plotter,
        Rect(18.0, 96.0, d.page_width - 36.0, 12.0),
        _mid("index"),
        "CONTROL  mid-page",
    )


def paint_side(plotter: Fpdf2Plotter, edge: str) -> None:
    d = plotter.device
    dest = f"probe-{edge}"
    plotter.begin_page()
    plotter.add_dest(dest)
    from_left = edge == "left"

    title_x = 8.0
    plotter.text(
        Rect(title_x, 6.0, d.page_width - 16.0, 10.0),
        f"{edge.upper()}  mm from glass  (32 already died)",
        ref=TypeRef(step="title"),
        gray=INK,
    )
    plotter.text(
        Rect(title_x, 16.0, d.page_width - 16.0, 8.0),
        "Tap the white slab. Number is not a hit. 80 mm is page centre.",
        ref=TypeRef(step="caption"),
        gray=MUTED,
    )

    n = len(SIDE_TARGETS)
    block = n * SIDE_H + (n - 1) * SIDE_GAP
    y_lo = 32.0
    label_w = 24.0
    for i, mm in enumerate(SIDE_TARGETS):
        y = y_lo + i * (SIDE_H + SIDE_GAP)
        if from_left:
            x = mm - BOX / 2.0
            slab = Rect(x, y, BOX, SIDE_H)
            # Label sits toward centre, never on the slab.
            num = Rect(min(mm + 6.0, d.page_width - label_w - 8.0), y, label_w, SIDE_H)
            lead_x0 = slab.right
            lead_x1 = num.x
            align = "left"
        else:
            x = d.page_width - mm - BOX / 2.0
            slab = Rect(x, y, BOX, SIDE_H)
            num = Rect(max(8.0, d.page_width - mm - 6.0 - label_w), y, label_w, SIDE_H)
            lead_x0 = slab.x
            lead_x1 = num.right
            align = "right"
        plotter.rect(slab, stroke=True, fill=True, stroke_width=0.22, fill_gray=1.0, stroke_gray=INK)
        mid_y = y + SIDE_H / 2.0
        plotter.line(lead_x0, mid_y, lead_x1, mid_y, stroke_width=0.18, stroke_gray=INK)
        plotter.rect(num, stroke=True, fill=True, stroke_width=0.18, fill_gray=WASH, stroke_gray=INK)
        plotter.text(
            num,
            f"{mm:g} mm",
            ref=TypeRef(step="label", emphasis="strong"),
            gray=INK,
            align=align,
        )
        plotter.link(slab, _dest(edge, mm))

    # CONTROL is page-centre so it stays out of EasyReach columns.
    ctrl = Rect(38.0, y_lo + block + 8.0, d.page_width - 76.0, 12.0)
    _control(plotter, ctrl, _mid(edge), "CONTROL  mid-page")
    back = Rect(38.0, y_lo + block + 24.0, d.page_width - 76.0, 10.0)
    plotter.rect(back, stroke=True, fill=False, stroke_width=0.18, stroke_gray=INK)
    plotter.text(back, "back to index", ref=TypeRef(step="chrome"), gray=INK, align="center", small_caps=True)
    plotter.link(back, "index")


def press_probe(output: Path) -> Path:
    plotter = Fpdf2Plotter(SCRIBE)
    plotter.reserve_dest("index")
    plotter.reserve_dest("probe-left")
    plotter.reserve_dest("probe-right")
    plotter.reserve_dest(_mid("index"))
    plotter.reserve_dest(_mid("left"))
    plotter.reserve_dest(_mid("right"))
    for mm in SIDE_TARGETS:
        plotter.reserve_dest(_dest("left", mm))
        plotter.reserve_dest(_dest("right", mm))

    paint_index(plotter)
    paint_hit(plotter, "HIT mid-page  index", _mid("index"), "index", "back to index")

    paint_side(plotter, "left")
    paint_hit(plotter, "HIT mid-page  left", _mid("left"), "probe-left", "back to left")
    for mm in SIDE_TARGETS:
        paint_hit(plotter, f"HIT LEFT {mm:g} mm", _dest("left", mm), "probe-left", "back to left")

    paint_side(plotter, "right")
    paint_hit(plotter, "HIT mid-page  right", _mid("right"), "probe-right", "back to right")
    for mm in SIDE_TARGETS:
        paint_hit(plotter, f"HIT RIGHT {mm:g} mm", _dest("right", mm), "probe-right", "back to right")

    plotter.finish(output)
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="scribe-side-depth-probe")
    parser.add_argument("-o", "--output", default="out/scribe-side-depth-probe.pdf")
    args = parser.parse_args(argv)
    path = press_probe(Path(args.output))
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
