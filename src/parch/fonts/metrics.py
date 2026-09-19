"""Measured TTF ink and the fpdf2 cap-height text seat.

``Fpdf2Plotter.text`` places a line by baseline, not ink center — a period
sits on that baseline while ``x`` / ``>`` / ``<`` nest higher. Key paint
reads those glyphs' ink boxes and shifts the draw box so nests coincide.
"""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

from parch.geom import Rect

_PT_MM = 25.4 / 72.0
# Same cap-height seat as ``Fpdf2Plotter.text`` / small-caps.
_CAP_EM = 0.72
_BASELINE_NUDGE_MM = 0.12


def pt_mm(pt: float) -> float:
    """PDF point → millimetre."""
    return pt * _PT_MM


def text_baseline(box: Rect, size_pt: float) -> float:
    """Y of ``fpdf.FPDF.text`` for one line cap-centered in ``box`` (y-down)."""
    cap = pt_mm(size_pt) * _CAP_EM
    return box.y + (box.h + cap) / 2.0 - _BASELINE_NUDGE_MM


def text_origin_x(box: Rect, advance_mm: float, *, align: str) -> float:
    """Left edge of the advance box — matches ``Fpdf2Plotter.text``."""
    match align:
        case "center":
            return box.x + (box.w - advance_mm) / 2.0
        case "right":
            return box.x + box.w - advance_mm
        case _:
            return box.x


@dataclass(frozen=True, slots=True)
class GlyphInk:
    """Ink bbox and advance in mm. ``y`` is font-space (+up from baseline)."""

    xmin: float
    ymin: float
    xmax: float
    ymax: float
    advance: float

    @property
    def cx(self) -> float:
        return (self.xmin + self.xmax) / 2.0

    @property
    def cy(self) -> float:
        return (self.ymin + self.ymax) / 2.0

    def nest(self, char: str) -> tuple[float, float]:
        """Bullet seat on this glyph: crotch of ``<>``, else ink center."""
        if char == ">":
            return self.xmin, self.cy
        if char == "<":
            return self.xmax, self.cy
        return self.cx, self.cy


@lru_cache(maxsize=8)
def _ttfont(path: str) -> TTFont:
    return TTFont(path)


@lru_cache(maxsize=128)
def glyph_ink(path: str, char: str, size_pt: float) -> GlyphInk:
    """Scale one character's TrueType ink into millimetres."""
    font = _ttfont(path)
    cmap = font.getBestCmap()
    name = cmap[ord(char)]
    glyphs = font.getGlyphSet()
    glyph = glyphs[name]
    pen = BoundsPen(glyphs)
    glyph.draw(pen)
    if pen.bounds is None:
        raise ValueError(f"no ink for {char!r} in {path}")
    scale = pt_mm(size_pt) / font["head"].unitsPerEm
    x0, y0, x1, y1 = pen.bounds
    return GlyphInk(
        xmin=x0 * scale,
        ymin=y0 * scale,
        xmax=x1 * scale,
        ymax=y1 * scale,
        advance=glyph.width * scale,
    )


def painted_nest(
    box: Rect,
    char: str,
    size_pt: float,
    path: str | Path,
    *,
    align: str = "center",
) -> tuple[float, float]:
    """Optical nest of ``char`` if seated in ``box`` like ``Fpdf2Plotter.text``."""
    ink = glyph_ink(str(path), char, size_pt)
    nx, ny = ink.nest(char)
    tx = text_origin_x(box, ink.advance, align=align)
    baseline = text_baseline(box, size_pt)
    return tx + nx, baseline - ny


def seat_box(
    box: Rect,
    char: str,
    size_pt: float,
    path: str | Path,
    seat: tuple[float, float],
    *,
    align: str = "center",
) -> Rect:
    """Shift ``box`` so ``char``'s nest lands on ``seat``."""
    cx, cy = painted_nest(box, char, size_pt, path, align=align)
    sx, sy = seat
    return Rect(box.x + (sx - cx), box.y + (sy - cy), box.w, box.h)
