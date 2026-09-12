"""Kindle Scribe left / right / top tap-zone probe. Not a product page.

Press:
    uv run python scripts/scribe_edge_probe.py -o out/scribe-edge-probe.pdf

Send-to-Kindle the PDF. Finger-tap (not pen). Each box is a named dest
whose centre sits N mm from the named glass edge. Confirm pages say
HIT TOP/LEFT/RIGHT N mm. Mid-page control should always work.

Page-turn / toolbar / no jump = still inside the OS or EasyReach band.

Fpdf2Plotter is top-left millimetres (same as the bottom-band probe):
y=0 is the top glass edge, x=0 is the left glass edge.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from parch.devices import SCRIBE
from parch.fonts.ramp import TypeRef
from parch.geom import Rect
from parch.plotter.fpdf2 import Fpdf2Plotter

# Top: include 26 mm (#193 discarded 1/8th = 26.25). Sides: include 8/12
# (#200 rail-clearance 8 + RAIL_PAD 4) and 32 in case EasyReach is fatter.
TOP_TARGETS = (2, 4, 6, 8, 10, 12, 16, 20, 24, 26, 30)
SIDE_TARGETS = (2, 4, 6, 8, 10, 12, 16, 20, 24, 32)
BOX = 3.2
INK = 0.0
MUTED = 112 / 255
WASH = 236 / 255
SOFT = 210 / 255


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
        "Scribe edge probe",
        ref=TypeRef(step="title"),
        gray=INK,
    )
    plotter.text(
        Rect(8.0, 18.5, d.page_width - 16.0, 6.0),
        f"{d.page_width:g} x {d.page_height:g} mm   1860x2480 @ 300 PPI",
        ref=TypeRef(step="caption"),
        gray=MUTED,
    )
    plotter.text(
        Rect(8.0, 26.0, d.page_width - 16.0, 16.0),
        "Send-to-Kindle. Finger tap, not pen. Link works = that distance "
        "from the named edge is above the OS / EasyReach band. Page-turn, "
        "toolbar, or no jump = still dead. Record Display Size + chrome up/down.",
        ref=TypeRef(step="body"),
        gray=INK,
    )
    plotter.text(
        Rect(8.0, 44.0, d.page_width - 16.0, 6.0),
        "Bottom already measured 10 mm. This file is top / left / right only.",
        ref=TypeRef(step="caption"),
        gray=MUTED,
    )

    nav = (
        ("TOP  0-30 mm", "probe-top"),
        ("LEFT  0-32 mm", "probe-left"),
        ("RIGHT  0-32 mm", "probe-right"),
    )
    slot = 14.0
    y0 = 56.0
    for i, (label, dest) in enumerate(nav):
        box = Rect(18.0, y0 + i * slot, d.page_width - 36.0, 12.0)
        plotter.rect(box, stroke=True, fill=True, stroke_width=0.22, fill_gray=WASH, stroke_gray=INK)
        plotter.text(box, label, ref=TypeRef(step="chrome"), gray=INK, align="center", small_caps=True)
        plotter.link(box, dest)

    _control(
        plotter,
        Rect(18.0, 110.0, d.page_width - 36.0, 12.0),
        _mid("index"),
        "CONTROL  mid-page",
    )


def paint_top(plotter: Fpdf2Plotter) -> None:
    d = plotter.device
    plotter.begin_page()
    plotter.add_dest("probe-top")

    wash_h = 30.0
    plotter.rect(
        Rect(0.0, 0.0, d.page_width, wash_h),
        stroke=False,
        fill=True,
        fill_gray=WASH,
    )
    plotter.line(0.0, 26.0, d.page_width, 26.0, stroke_width=0.18, stroke_gray=SOFT)
    plotter.line(0.0, 8.0, d.page_width, 8.0, stroke_width=0.18, stroke_gray=SOFT)

    plotter.text(
        Rect(8.0, 34.0, d.page_width - 16.0, 8.0),
        "TOP  mm from glass",
        ref=TypeRef(step="title"),
        gray=INK,
    )
    plotter.text(
        Rect(8.0, 42.0, d.page_width - 16.0, 6.0),
        "#193 1/8th = 26.25 mm dashed. Toolbar lives up here on Send-to-Kindle.",
        ref=TypeRef(step="caption"),
        gray=MUTED,
    )

    ruler_x = 4.0
    for mm in range(0, 33):
        y = float(mm)
        tick = 5.0 if mm % 4 == 0 else 2.4
        plotter.line(ruler_x, y, ruler_x + tick, y, stroke_width=0.12 if mm % 2 else 0.18, stroke_gray=INK)
        if mm % 4 == 0:
            plotter.text(
                Rect(ruler_x + 5.4, y - 2.2, 12.0, 4.4),
                f"{mm}",
                ref=TypeRef(step="micro"),
                gray=INK,
            )

    slot = (d.page_width - 28.0) / len(TOP_TARGETS)
    for i, mm in enumerate(TOP_TARGETS):
        y = mm - BOX / 2.0
        box = Rect(22.0 + i * slot, y, slot - 1.2, BOX)
        plotter.rect(box, stroke=True, fill=True, stroke_width=0.18, fill_gray=1.0, stroke_gray=INK)
        plotter.text(box, f"{mm:g}", ref=TypeRef(step="label", emphasis="strong"), gray=INK, align="center")
        plotter.link(box, _dest("top", mm))

    _control(
        plotter,
        Rect(18.0, 90.0, d.page_width - 36.0, 12.0),
        _mid("top"),
        "CONTROL  mid-page",
    )
    back = Rect(18.0, 108.0, d.page_width - 36.0, 10.0)
    plotter.rect(back, stroke=True, fill=False, stroke_width=0.18, stroke_gray=INK)
    plotter.text(back, "back to index", ref=TypeRef(step="chrome"), gray=INK, align="center", small_caps=True)
    plotter.link(back, "index")


def paint_side(plotter: Fpdf2Plotter, edge: str) -> None:
    d = plotter.device
    dest = f"probe-{edge}"
    plotter.begin_page()
    plotter.add_dest(dest)

    from_left = edge == "left"
    wash_w = 32.0
    wash_x = 0.0 if from_left else d.page_width - wash_w
    # Keep wash off the measured 10 mm bottom and the top 16 mm toolbar guess.
    plotter.rect(
        Rect(wash_x, 16.0, wash_w, d.page_height - 36.0),
        stroke=False,
        fill=True,
        fill_gray=WASH,
    )
    mark_8 = 8.0 if from_left else d.page_width - 8.0
    mark_12 = 12.0 if from_left else d.page_width - 12.0
    plotter.line(mark_8, 16.0, mark_8, d.page_height - 20.0, stroke_width=0.18, stroke_gray=SOFT)
    plotter.line(mark_12, 16.0, mark_12, d.page_height - 20.0, stroke_width=0.18, stroke_gray=SOFT)

    title_x = 40.0 if from_left else 8.0
    title_w = d.page_width - 48.0
    plotter.text(
        Rect(title_x, 8.0, title_w, 10.0),
        f"{edge.upper()}  mm from glass",
        ref=TypeRef(step="title"),
        gray=INK,
    )
    plotter.text(
        Rect(title_x, 18.0, title_w, 6.0),
        "#200 rail 8 mm + pad 4 mm. Boxes sit mid-height, above the 10 mm bottom.",
        ref=TypeRef(step="caption"),
        gray=MUTED,
    )

    # 1 mm ticks along the measured edge, drawn through mid-page.
    tick_y = d.page_height / 2.0
    for mm in range(0, 37):
        x = mm if from_left else d.page_width - mm
        tick = 5.0 if mm % 4 == 0 else 2.4
        plotter.line(x, tick_y, x, tick_y + tick, stroke_width=0.12 if mm % 2 else 0.18, stroke_gray=INK)
        if mm % 4 == 0:
            label_x = (x + 1.2) if from_left else (x - 13.0)
            plotter.text(
                Rect(label_x, tick_y + tick + 0.4, 12.0, 4.4),
                f"{mm}",
                ref=TypeRef(step="micro"),
                gray=INK,
                align="left" if from_left else "right",
            )

    # Stack targets in the middle third so top toolbar and bottom OS band
    # do not confound the reading.
    y_lo = 70.0
    y_hi = 150.0
    span = y_hi - y_lo
    slot = span / len(SIDE_TARGETS)
    for i, mm in enumerate(SIDE_TARGETS):
        y = y_lo + i * slot
        if from_left:
            x = mm - BOX / 2.0
        else:
            x = d.page_width - mm - BOX / 2.0
        box = Rect(x, y, BOX, 10.0)
        plotter.rect(box, stroke=True, fill=True, stroke_width=0.18, fill_gray=1.0, stroke_gray=INK)
        num_w = 14.0
        if from_left:
            num = Rect(x + BOX + 1.2, y, num_w, 10.0)
            align = "left"
        else:
            num = Rect(x - num_w - 1.2, y, num_w, 10.0)
            align = "right"
        plotter.text(num, f"{mm:g}", ref=TypeRef(step="label", emphasis="strong"), gray=INK, align=align)
        plotter.link(box, _dest(edge, mm))

    ctrl_x = 48.0 if from_left else 18.0
    _control(
        plotter,
        Rect(ctrl_x, 168.0, d.page_width - 66.0, 12.0),
        _mid(edge),
        "CONTROL  mid-page",
    )
    back = Rect(ctrl_x, 184.0, d.page_width - 66.0, 10.0)
    plotter.rect(back, stroke=True, fill=False, stroke_width=0.18, stroke_gray=INK)
    plotter.text(back, "back to index", ref=TypeRef(step="chrome"), gray=INK, align="center", small_caps=True)
    plotter.link(back, "index")


def press_probe(output: Path) -> Path:
    plotter = Fpdf2Plotter(SCRIBE)
    plotter.reserve_dest("index")
    plotter.reserve_dest("probe-top")
    plotter.reserve_dest("probe-left")
    plotter.reserve_dest("probe-right")
    plotter.reserve_dest(_mid("index"))
    plotter.reserve_dest(_mid("top"))
    plotter.reserve_dest(_mid("left"))
    plotter.reserve_dest(_mid("right"))
    for mm in TOP_TARGETS:
        plotter.reserve_dest(_dest("top", mm))
    for mm in SIDE_TARGETS:
        plotter.reserve_dest(_dest("left", mm))
        plotter.reserve_dest(_dest("right", mm))

    paint_index(plotter)
    paint_hit(plotter, "HIT mid-page  index", _mid("index"), "index", "back to index")

    paint_top(plotter)
    paint_hit(plotter, "HIT mid-page  top", _mid("top"), "probe-top", "back to top")
    for mm in TOP_TARGETS:
        paint_hit(plotter, f"HIT TOP {mm:g} mm", _dest("top", mm), "probe-top", "back to top")

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
    parser = argparse.ArgumentParser(prog="scribe-edge-probe")
    parser.add_argument("-o", "--output", default="out/scribe-edge-probe.pdf")
    args = parser.parse_args(argv)
    path = press_probe(Path(args.output))
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
