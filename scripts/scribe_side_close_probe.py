"""Kindle Scribe side-column size + how-close-to-glass probe.

Press:
    uv run python scripts/scribe_side_close_probe.py -o out/scribe-side-close-probe.pdf

Prior: mid-page 4–40 mm all HIT. Fat 24×14 at 32–80 mm all HIT.
3.2 mm slivers in the side column page-turned.

SIZE pages: box centres sit at 44 mm from that glass so a 24 mm box
lives in the already-good [32, 56] band. Widths 4/8/12/16/24/40.
Answers which widths work IN the EasyReach column.

EDGE pages: 24×14 outline for a finger pad. Only a 4×14 filled
stripe is linked. Near edge of the stripe is N mm from the glass.
N = 4/8/12/16/20/24/32. HIT N = that inset is live at 4 mm width.

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
EDGE_INSETS = (4, 8, 12, 16, 20, 24, 32)
SIZE_CENTER = 44.0
STRIPE = 4.0
PAD_W = 24.0
BOX_H = 14.0
GAP = 5.0
INK = 0.0
MUTED = 112 / 255
WASH = 236 / 255
SOFT = 210 / 255


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
        "Scribe side close probe",
        ref=TypeRef(step="title"),
        gray=INK,
    )
    plotter.text(
        Rect(8.0, 18.5, d.page_width - 16.0, 6.0),
        "Which widths work in the side column, and how close to the glass.",
        ref=TypeRef(step="caption"),
        gray=MUTED,
    )
    plotter.text(
        Rect(8.0, 26.0, d.page_width - 16.0, 16.0),
        "Send-to-Kindle. SIZE: tap the white box (centred at 44 mm). "
        "EDGE: tap the filled stripe, not the outline pad. CONTROL first.",
        ref=TypeRef(step="body"),
        gray=INK,
    )

    nav = (
        ("SIZE LEFT  4-40 mm at 44 mm", "probe-size-left"),
        ("SIZE RIGHT  4-40 mm at 44 mm", "probe-size-right"),
        ("EDGE LEFT  4-32 mm stripe", "probe-edge-left"),
        ("EDGE RIGHT  4-32 mm stripe", "probe-edge-right"),
    )
    y0 = 48.0
    for i, (label, dest) in enumerate(nav):
        box = Rect(18.0, y0 + i * 15.0, d.page_width - 36.0, 12.0)
        plotter.rect(box, stroke=True, fill=True, stroke_width=0.22, fill_gray=WASH, stroke_gray=INK)
        plotter.text(box, label, ref=TypeRef(step="chrome"), gray=INK, align="center", small_caps=True)
        plotter.link(box, dest)

    _control(
        plotter,
        Rect(18.0, 116.0, d.page_width - 36.0, 12.0),
        _mid("index"),
        "CONTROL  mid-page",
    )


def paint_size_side(plotter: Fpdf2Plotter, edge: str) -> None:
    d = plotter.device
    dest = f"probe-size-{edge}"
    plotter.begin_page()
    plotter.add_dest(dest)
    from_left = edge == "left"
    plotter.text(
        Rect(8.0, 6.0, d.page_width - 16.0, 10.0),
        f"SIZE {edge.upper()}  centre = 44 mm from glass",
        ref=TypeRef(step="title"),
        gray=INK,
    )
    plotter.text(
        Rect(8.0, 16.0, d.page_width - 16.0, 8.0),
        "Tap the white box. Label is not a hit.",
        ref=TypeRef(step="caption"),
        gray=MUTED,
    )

    n = len(SIZE_WIDTHS)
    block = n * BOX_H + (n - 1) * GAP
    y_lo = 30.0
    cx = SIZE_CENTER if from_left else d.page_width - SIZE_CENTER
    for i, w in enumerate(SIZE_WIDTHS):
        y = y_lo + i * (BOX_H + GAP)
        box = Rect(cx - w / 2.0, y, w, BOX_H)
        plotter.rect(box, stroke=True, fill=True, stroke_width=0.22, fill_gray=1.0, stroke_gray=INK)
        if from_left:
            lab = Rect(cx + 24.0, y, 40.0, BOX_H)
            align = "left"
        else:
            lab = Rect(cx - 24.0 - 40.0, y, 40.0, BOX_H)
            align = "right"
        plotter.text(
            lab,
            f"{w:g} mm",
            ref=TypeRef(step="label", emphasis="strong"),
            gray=INK,
            align=align,
        )
        plotter.link(box, _dest(f"size-{edge}", w))

    _control(
        plotter,
        Rect(38.0, y_lo + block + 8.0, d.page_width - 76.0, 12.0),
        _mid(f"size-{edge}"),
        "CONTROL  mid-page",
    )
    back = Rect(38.0, y_lo + block + 24.0, d.page_width - 76.0, 10.0)
    plotter.rect(back, stroke=True, fill=False, stroke_width=0.18, stroke_gray=INK)
    plotter.text(back, "back to index", ref=TypeRef(step="chrome"), gray=INK, align="center", small_caps=True)
    plotter.link(back, "index")


def paint_edge(plotter: Fpdf2Plotter, edge: str) -> None:
    d = plotter.device
    dest = f"probe-edge-{edge}"
    plotter.begin_page()
    plotter.add_dest(dest)
    from_left = edge == "left"
    plotter.text(
        Rect(8.0, 6.0, d.page_width - 16.0, 10.0),
        f"EDGE {edge.upper()}  tap the filled stripe",
        ref=TypeRef(step="title"),
        gray=INK,
    )
    plotter.text(
        Rect(8.0, 16.0, d.page_width - 16.0, 8.0),
        "Outline is a finger pad, not a link. Stripe near-edge = N mm.",
        ref=TypeRef(step="caption"),
        gray=MUTED,
    )

    n = len(EDGE_INSETS)
    block = n * BOX_H + (n - 1) * GAP
    y_lo = 30.0
    for i, mm in enumerate(EDGE_INSETS):
        y = y_lo + i * (BOX_H + GAP)
        if from_left:
            stripe = Rect(mm, y, STRIPE, BOX_H)
            pad = Rect(mm, y, PAD_W, BOX_H)
            lab = Rect(mm + PAD_W + 4.0, y, 40.0, BOX_H)
            align = "left"
        else:
            stripe = Rect(d.page_width - mm - STRIPE, y, STRIPE, BOX_H)
            pad = Rect(d.page_width - mm - PAD_W, y, PAD_W, BOX_H)
            lab = Rect(d.page_width - mm - PAD_W - 44.0, y, 40.0, BOX_H)
            align = "right"
        plotter.rect(pad, stroke=True, fill=False, stroke_width=0.18, stroke_gray=SOFT)
        plotter.rect(stripe, stroke=True, fill=True, stroke_width=0.22, fill_gray=1.0, stroke_gray=INK)
        plotter.text(
            lab,
            f"{mm:g} mm",
            ref=TypeRef(step="label", emphasis="strong"),
            gray=INK,
            align=align,
        )
        plotter.link(stripe, _dest(f"edge-{edge}", mm))

    _control(
        plotter,
        Rect(38.0, y_lo + block + 8.0, d.page_width - 76.0, 12.0),
        _mid(f"edge-{edge}"),
        "CONTROL  mid-page",
    )
    back = Rect(38.0, y_lo + block + 24.0, d.page_width - 76.0, 10.0)
    plotter.rect(back, stroke=True, fill=False, stroke_width=0.18, stroke_gray=INK)
    plotter.text(back, "back to index", ref=TypeRef(step="chrome"), gray=INK, align="center", small_caps=True)
    plotter.link(back, "index")


def press_probe(output: Path) -> Path:
    plotter = Fpdf2Plotter(SCRIBE)
    plotter.reserve_dest("index")
    for kind in ("index", "size-left", "size-right", "edge-left", "edge-right"):
        plotter.reserve_dest(_mid(kind))
    plotter.reserve_dest("probe-size-left")
    plotter.reserve_dest("probe-size-right")
    plotter.reserve_dest("probe-edge-left")
    plotter.reserve_dest("probe-edge-right")
    for w in SIZE_WIDTHS:
        plotter.reserve_dest(_dest("size-left", w))
        plotter.reserve_dest(_dest("size-right", w))
    for mm in EDGE_INSETS:
        plotter.reserve_dest(_dest("edge-left", mm))
        plotter.reserve_dest(_dest("edge-right", mm))

    paint_index(plotter)
    paint_hit(plotter, "HIT mid-page  index", _mid("index"), "index", "back to index")

    paint_size_side(plotter, "left")
    paint_hit(plotter, "HIT mid-page  size left", _mid("size-left"), "probe-size-left", "back to size left")
    for w in SIZE_WIDTHS:
        paint_hit(plotter, f"HIT SIZE LEFT {w:g} mm", _dest("size-left", w), "probe-size-left", "back to size left")

    paint_size_side(plotter, "right")
    paint_hit(plotter, "HIT mid-page  size right", _mid("size-right"), "probe-size-right", "back to size right")
    for w in SIZE_WIDTHS:
        paint_hit(plotter, f"HIT SIZE RIGHT {w:g} mm", _dest("size-right", w), "probe-size-right", "back to size right")

    paint_edge(plotter, "left")
    paint_hit(plotter, "HIT mid-page  edge left", _mid("edge-left"), "probe-edge-left", "back to edge left")
    for mm in EDGE_INSETS:
        paint_hit(plotter, f"HIT EDGE LEFT {mm:g} mm", _dest("edge-left", mm), "probe-edge-left", "back to edge left")

    paint_edge(plotter, "right")
    paint_hit(plotter, "HIT mid-page  edge right", _mid("edge-right"), "probe-edge-right", "back to edge right")
    for mm in EDGE_INSETS:
        paint_hit(plotter, f"HIT EDGE RIGHT {mm:g} mm", _dest("edge-right", mm), "probe-edge-right", "back to edge right")

    plotter.finish(output)
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="scribe-side-close-probe")
    parser.add_argument("-o", "--output", default="out/scribe-side-close-probe.pdf")
    args = parser.parse_args(argv)
    path = press_probe(Path(args.output))
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
