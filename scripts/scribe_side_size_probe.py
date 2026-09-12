"""Kindle Scribe side size-vs-position probe.

Press:
    uv run python scripts/scribe_side_size_probe.py -o out/scribe-side-size-probe.pdf

Hypothesis: 3.2 mm slabs died because Kindle will not honour a tiny
link in EasyReach, not because the whole half-page is dead. CONTROL
(wide mid-page) always works. This file splits the two variables.

SIZE page: every box is centred on page mid (x = 78.74). Widths
4 / 8 / 12 / 16 / 24 / 40 mm. If 4 dies and 16+ HIT, min size is real.

LEFT / RIGHT pages: every box is 24 x 14 mm. Near edge at
32 / 40 / 48 / 56 / 64 / 80 mm from that glass. HIT = a CONTROL-class
target at that inset is usable.

Fpdf2Plotter is top-left millimetres.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from parch.devices import SCRIBE
from parch.fonts.ramp import TypeRef
from parch.geom import Rect
from parch.plotter.fpdf2 import Fpdf2Plotter

SIZE_WIDTHS = (4, 8, 12, 16, 24, 40)
POS_INSETS = (32, 40, 48, 56, 64, 80)
POS_W = 24.0
BOX_H = 14.0
GAP = 6.0
INK = 0.0
MUTED = 112 / 255
WASH = 236 / 255


def _dest(kind: str, n: float) -> str:
    return f"hit-{kind}-{n:g}".replace(".", "p")


def _mid(kind: str) -> str:
    return f"hit-{kind}-mid"


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
        "Scribe side size probe",
        ref=TypeRef(step="title"),
        gray=INK,
    )
    plotter.text(
        Rect(8.0, 18.5, d.page_width - 16.0, 6.0),
        "3.2 mm slabs died even at CONTROL X. Split size vs inset.",
        ref=TypeRef(step="caption"),
        gray=MUTED,
    )
    plotter.text(
        Rect(8.0, 26.0, d.page_width - 16.0, 18.0),
        "Send-to-Kindle. Finger or stylus hand-tool. SIZE first: all boxes "
        "sit on the page centre line. Then LEFT / RIGHT: fat boxes whose "
        "near edge is N mm from that glass. CONTROL must work on every page.",
        ref=TypeRef(step="body"),
        gray=INK,
    )

    nav = (
        ("SIZE  mid-page  4-40 mm wide", "probe-size"),
        ("LEFT  fat box  32-80 mm", "probe-left"),
        ("RIGHT  fat box  32-80 mm", "probe-right"),
    )
    y0 = 52.0
    for i, (label, dest) in enumerate(nav):
        box = Rect(18.0, y0 + i * 16.0, d.page_width - 36.0, 12.0)
        plotter.rect(box, stroke=True, fill=True, stroke_width=0.22, fill_gray=WASH, stroke_gray=INK)
        plotter.text(box, label, ref=TypeRef(step="chrome"), gray=INK, align="center", small_caps=True)
        plotter.link(box, dest)

    _control(
        plotter,
        Rect(18.0, 110.0, d.page_width - 36.0, 12.0),
        _mid("index"),
        "CONTROL  mid-page",
    )


def paint_size(plotter: Fpdf2Plotter) -> None:
    d = plotter.device
    plotter.begin_page()
    plotter.add_dest("probe-size")
    mid = d.page_width / 2.0
    plotter.text(
        Rect(8.0, 6.0, d.page_width - 16.0, 10.0),
        "SIZE  centred on page mid",
        ref=TypeRef(step="title"),
        gray=INK,
    )
    plotter.text(
        Rect(8.0, 16.0, d.page_width - 16.0, 8.0),
        "Same X as CONTROL. Only the width changes. Tap the white box.",
        ref=TypeRef(step="caption"),
        gray=MUTED,
    )

    n = len(SIZE_WIDTHS)
    block = n * BOX_H + (n - 1) * GAP
    y_lo = 30.0
    for i, w in enumerate(SIZE_WIDTHS):
        y = y_lo + i * (BOX_H + GAP)
        box = Rect(mid - w / 2.0, y, w, BOX_H)
        plotter.rect(box, stroke=True, fill=True, stroke_width=0.22, fill_gray=1.0, stroke_gray=INK)
        # Label sits left of the stack so it is not a hit on the box.
        lab = Rect(8.0, y, 28.0, BOX_H)
        plotter.text(
            lab,
            f"{w:g} mm",
            ref=TypeRef(step="label", emphasis="strong"),
            gray=INK,
            align="left",
        )
        plotter.link(box, _dest("size", w))

    _control(
        plotter,
        Rect(18.0, y_lo + block + 8.0, d.page_width - 36.0, 12.0),
        _mid("size"),
        "CONTROL  mid-page",
    )
    back = Rect(18.0, y_lo + block + 24.0, d.page_width - 36.0, 10.0)
    plotter.rect(back, stroke=True, fill=False, stroke_width=0.18, stroke_gray=INK)
    plotter.text(back, "back to index", ref=TypeRef(step="chrome"), gray=INK, align="center", small_caps=True)
    plotter.link(back, "index")


def paint_pos(plotter: Fpdf2Plotter, edge: str) -> None:
    d = plotter.device
    plotter.begin_page()
    plotter.add_dest(f"probe-{edge}")
    from_left = edge == "left"
    plotter.text(
        Rect(8.0, 6.0, d.page_width - 16.0, 10.0),
        f"{edge.upper()}  fat box  near edge = N mm",
        ref=TypeRef(step="title"),
        gray=INK,
    )
    plotter.text(
        Rect(8.0, 16.0, d.page_width - 16.0, 8.0),
        "24 x 14 mm. Tap the white box. Label is not a hit.",
        ref=TypeRef(step="caption"),
        gray=MUTED,
    )

    n = len(POS_INSETS)
    block = n * BOX_H + (n - 1) * GAP
    y_lo = 30.0
    for i, mm in enumerate(POS_INSETS):
        y = y_lo + i * (BOX_H + GAP)
        if from_left:
            box = Rect(mm, y, POS_W, BOX_H)
            lab = Rect(mm + POS_W + 4.0, y, 36.0, BOX_H)
            align = "left"
        else:
            box = Rect(d.page_width - mm - POS_W, y, POS_W, BOX_H)
            lab = Rect(d.page_width - mm - POS_W - 40.0, y, 36.0, BOX_H)
            align = "right"
        plotter.rect(box, stroke=True, fill=True, stroke_width=0.22, fill_gray=1.0, stroke_gray=INK)
        plotter.text(
            lab,
            f"{mm:g} mm",
            ref=TypeRef(step="label", emphasis="strong"),
            gray=INK,
            align=align,
        )
        plotter.link(box, _dest(edge, mm))

    _control(
        plotter,
        Rect(28.0, y_lo + block + 8.0, d.page_width - 56.0, 12.0),
        _mid(edge),
        "CONTROL  mid-page",
    )
    back = Rect(28.0, y_lo + block + 24.0, d.page_width - 56.0, 10.0)
    plotter.rect(back, stroke=True, fill=False, stroke_width=0.18, stroke_gray=INK)
    plotter.text(back, "back to index", ref=TypeRef(step="chrome"), gray=INK, align="center", small_caps=True)
    plotter.link(back, "index")


def press_probe(output: Path) -> Path:
    plotter = Fpdf2Plotter(SCRIBE)
    plotter.reserve_dest("index")
    plotter.reserve_dest("probe-size")
    plotter.reserve_dest("probe-left")
    plotter.reserve_dest("probe-right")
    for kind in ("index", "size", "left", "right"):
        plotter.reserve_dest(_mid(kind))
    for w in SIZE_WIDTHS:
        plotter.reserve_dest(_dest("size", w))
    for mm in POS_INSETS:
        plotter.reserve_dest(_dest("left", mm))
        plotter.reserve_dest(_dest("right", mm))

    paint_index(plotter)
    paint_hit(plotter, "HIT mid-page  index", _mid("index"), "index", "back to index")

    paint_size(plotter)
    paint_hit(plotter, "HIT mid-page  size", _mid("size"), "probe-size", "back to size")
    for w in SIZE_WIDTHS:
        paint_hit(plotter, f"HIT SIZE {w:g} mm wide", _dest("size", w), "probe-size", "back to size")

    paint_pos(plotter, "left")
    paint_hit(plotter, "HIT mid-page  left", _mid("left"), "probe-left", "back to left")
    for mm in POS_INSETS:
        paint_hit(plotter, f"HIT LEFT {mm:g} mm", _dest("left", mm), "probe-left", "back to left")

    paint_pos(plotter, "right")
    paint_hit(plotter, "HIT mid-page  right", _mid("right"), "probe-right", "back to right")
    for mm in POS_INSETS:
        paint_hit(plotter, f"HIT RIGHT {mm:g} mm", _dest("right", mm), "probe-right", "back to right")

    plotter.finish(output)
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="scribe-side-size-probe")
    parser.add_argument("-o", "--output", default="out/scribe-side-size-probe.pdf")
    args = parser.parse_args(argv)
    path = press_probe(Path(args.output))
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
