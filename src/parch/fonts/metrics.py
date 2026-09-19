"""Vendored-face ink bounds (fontTools) and the fpdf2 cap-height text seat.

Key marks read the Jost cut ``FontCatalog`` already bound on the ramp
(``jost_catalog()`` — the same TTF ``TypeRef`` weight resolves). BoundsPen
walks that file's outline; we do not stroke paths or fetch a remote face.
``Fpdf2Plotter.text`` still places ordinary lines by baseline. Compose uses
``origin_for_nest`` so a glyph's ink nest lands on a shared seat.
"""

from dataclasses import dataclass
from functools import lru_cache

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


@dataclass(frozen=True, slots=True)
class GlyphInk:
    """Ink bbox in mm. ``y`` is font-space (+up from baseline)."""

    xmin: float
    ymin: float
    xmax: float
    ymax: float

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
    )


def origin_for_nest(
    seat: tuple[float, float], ink: GlyphInk, char: str
) -> tuple[float, float]:
    """fpdf2 ``text(x, baseline)`` so ``ink.nest(char)`` lands on ``seat`` (y-down)."""
    nx, ny = ink.nest(char)
    sx, sy = seat
    return sx - nx, sy + ny


def ink_rect(seat: tuple[float, float], ink: GlyphInk, char: str) -> Rect:
    """Page-space ink box when the nest is on ``seat`` (y-down)."""
    nx, ny = ink.nest(char)
    sx, sy = seat
    return Rect(
        sx - (nx - ink.xmin),
        sy - (ink.ymax - ny),
        ink.xmax - ink.xmin,
        ink.ymax - ink.ymin,
    )
