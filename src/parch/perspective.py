"""Edge-to-edge perspective grid. Pad-only has no cover; a notebook may prefix one.

Square grid lines sit on the half-pitch lattice around the page center, so the
vanishing point is the center of a square and opposite edges share one fall-off:

    x = cx + (k + 1/2) · p
    y = cy + (k + 1/2) · p

Each perspective line is the page chord through that center and one outer grid
corner: the top intersection of every vertical line, and the left intersection
of every horizontal line. Corners that share a direction are one line. Lines
are sorted by angle and alternate dark, light.
"""

import math
from dataclasses import dataclass

from parch.components.perspective import PerspectivePad
from parch.geom import Rect
from parch.sections.page import Page
from parch.spec import Spec


@dataclass(frozen=True, slots=True)
class PerspectiveRay:
    """One undirected chord of the page through the vanishing point."""

    x1: float
    y1: float
    x2: float
    y2: float
    dark: bool


@dataclass(frozen=True, slots=True)
class PerspectiveMesh:
    """Full-bleed square grid plus vanishing-point chords. No frame."""

    pitch: float
    cx: float
    cy: float
    verticals: tuple[float, ...]
    horizontals: tuple[float, ...]
    rays: tuple[PerspectiveRay, ...]


def perspective_falloff(
    mesh: PerspectiveMesh, box: Rect
) -> tuple[float, float, float, float]:
    """Partial square outside the outer grid lines: left, right, top, bottom."""
    return (
        mesh.verticals[0] - box.x,
        box.right - mesh.verticals[-1],
        mesh.horizontals[0] - box.y,
        box.bottom - mesh.horizontals[-1],
    )


def perspective_mesh(box: Rect, pitch: float) -> PerspectiveMesh:
    """Grid and rays for *box*. ``pitch`` is the square size (engineering 5 mm).

    Vertical indices ``k`` and horizontal indices ``m`` are the integers in
    ``center + (index + 1/2) · pitch`` that still meet the page. Outer corners
    are ``(x_k, y_{m_min})`` and ``(x_{k_min}, y_m)``. The direction of a
    corner is the odd pair ``(2k+1, 2m+1)`` reduced by ``gcd``, with the first
    component kept positive so each undirected line is stored once. The chord
    is that line clipped to *box*.
    """
    cx = box.x + box.w / 2
    cy = box.y + box.h / 2
    ks = _indices(cx, box.x, box.right, pitch)
    ms = _indices(cy, box.y, box.bottom, pitch)
    verticals = tuple(cx + (k + 0.5) * pitch for k in ks)
    horizontals = tuple(cy + (m + 0.5) * pitch for m in ms)
    rays = _rays(cx, cy, ks, ms, box)
    return PerspectiveMesh(pitch, cx, cy, verticals, horizontals, rays)


def perspective_pages(spec: Spec) -> list[Page]:
    """One full-bleed perspective face per ``perspective_sheets``. Empty when 0.

    Exclusive pad-only when this count is > 0 on year-planner and other pad
    counts stay 0. Year-planner mix with other pads raises ``ConfigError`` —
    this helper stays empty-safe.
    """
    built: list[Page] = []
    for sheet in range(1, spec.perspective_sheets + 1):
        built.append(
            Page(
                dest=spec.dest_for_perspective_pad(sheet),
                kind="perspective",
                title="Perspective",
                nav=(),
                components=(
                    PerspectivePad(sheet=sheet, sheets=spec.perspective_sheets),
                ),
            )
        )
    return built


def _indices(center: float, lo: float, hi: float, pitch: float) -> tuple[int, ...]:
    """Integers k with ``lo <= center + (k + 1/2) · pitch <= hi``."""
    k_min = math.ceil((lo - center) / pitch - 0.5 - 1e-9)
    k_max = math.floor((hi - center) / pitch - 0.5 + 1e-9)
    found: list[int] = []
    for k in range(k_min, k_max + 1):
        pos = center + (k + 0.5) * pitch
        if lo - 1e-6 <= pos <= hi + 1e-6:
            found.append(k)
    return tuple(found)


def _reduce(a: int, b: int) -> tuple[int, int]:
    g = math.gcd(a, b)
    a //= g
    b //= g
    if a < 0:
        a, b = -a, -b
    return a, b


def _rays(
    cx: float,
    cy: float,
    ks: tuple[int, ...],
    ms: tuple[int, ...],
    box: Rect,
) -> tuple[PerspectiveRay, ...]:
    k0 = ks[0]
    m0 = ms[0]
    dirs: set[tuple[int, int]] = set()
    for k in ks:
        dirs.add(_reduce(2 * k + 1, 2 * m0 + 1))
    for m in ms:
        dirs.add(_reduce(2 * k0 + 1, 2 * m + 1))
    ordered = sorted(dirs, key=lambda ab: math.atan2(ab[1], ab[0]))
    rays: list[PerspectiveRay] = []
    for i, (a, b) in enumerate(ordered):
        x1, y1, x2, y2 = _clip_chord(cx, cy, float(a), float(b), box)
        rays.append(PerspectiveRay(x1, y1, x2, y2, dark=(i % 2 == 0)))
    return tuple(rays)


def _snap(value: float, lo: float, hi: float) -> float:
    if abs(value - lo) <= 1e-6:
        return lo
    if abs(value - hi) <= 1e-6:
        return hi
    return value


def _clip_chord(
    cx: float, cy: float, dx: float, dy: float, box: Rect
) -> tuple[float, float, float, float]:
    """Page chord through ``(cx, cy)`` in direction ``(dx, dy)``."""
    spans: list[tuple[float, float, float]] = []
    if dx != 0.0:
        for x_edge in (box.x, box.right):
            t = (x_edge - cx) / dx
            y = cy + t * dy
            if box.y - 1e-6 <= y <= box.bottom + 1e-6:
                spans.append((t, x_edge, _snap(y, box.y, box.bottom)))
    if dy != 0.0:
        for y_edge in (box.y, box.bottom):
            t = (y_edge - cy) / dy
            x = cx + t * dx
            if box.x - 1e-6 <= x <= box.right + 1e-6:
                spans.append((t, _snap(x, box.x, box.right), y_edge))
    neg = [item for item in spans if item[0] < 0.0]
    pos = [item for item in spans if item[0] > 0.0]
    if not neg or not pos:
        raise ValueError("perspective ray does not cross the page")
    _tn, x1, y1 = max(neg, key=lambda item: item[0])
    _tp, x2, y2 = min(pos, key=lambda item: item[0])
    return x1, y1, x2, y2
