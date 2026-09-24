"""Edge-to-edge perspective grid. Pad-only has no cover; a notebook may prefix one.

Square grid lines sit on the half-pitch lattice around the page center, so the
vanishing point is the center of a square and opposite edges share one fall-off:

    x = cx + (k + 1/2) · p
    y = cy + (k + 1/2) · p

Each perspective chord runs edge to edge through that center and one grid
line where it meets the page (vertical lines at the top edge, horizontal
lines at the left edge). The half-pitch index is ``h = 2k + 1`` (the line
sits at ``center + h · p/2``). ``|h| = 1`` is the crossing nearest each axis.
Keeping ``|h| ≡ 1 (mod 4)`` takes those nearest crossings and then every
second pair outward. ``h`` and ``-h`` stay together, so the fan mirrors
left/right and top/bottom.

Even ``|k|`` does not: it keeps the nearest line on the positive side
(``k = 0``) and skips the nearest line on the negative side (``k = -1``).

The horizontal and vertical lines through the vanishing point are extra
chords (they are not grid lines). Chords are sorted by undirected angle.
Even positions are dark; the vertical axis lands on an odd position because
mirror pairs fill ``(0°, 90°)`` evenly, so that axis is forced dark.
"""

import math
from dataclasses import dataclass

from parch.components.perspective import PerspectivePad
from parch.geom import Rect
from parch.sections.page import Page
from parch.spec import Spec

# This page only. Not a Spec/TOML knob, and not the engineering/dotgrid pitch.
PERSPECTIVE_PITCH_MM = 7.0


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


def perspective_mesh(box: Rect, pitch: float = PERSPECTIVE_PITCH_MM) -> PerspectiveMesh:
    """Grid and rays for *box*. ``pitch`` defaults to this page's 7 mm square.

    Grid indices are the integers in ``center + (index + 1/2) · pitch`` that
    still meet the page. Rays are edge-to-edge chords through every second
    grid-line/edge crossing (``|2k+1| ≡ 1 (mod 4)``) plus the two axes.
    """
    cx = box.x + box.w / 2
    cy = box.y + box.h / 2
    ks = _indices(cx, box.x, box.right, pitch)
    ms = _indices(cy, box.y, box.bottom, pitch)
    verticals = tuple(cx + (k + 0.5) * pitch for k in ks)
    horizontals = tuple(cy + (m + 0.5) * pitch for m in ms)
    rays = _rays(cx, cy, ks, ms, pitch, box)
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


def _every_second(indices: tuple[int, ...]) -> tuple[int, ...]:
    """Indices whose half-pitch ``|2k+1| ≡ 1 (mod 4)``: nearest, then every second."""
    return tuple(k for k in indices if abs(2 * k + 1) % 4 == 1)


def _rays(
    cx: float,
    cy: float,
    ks: tuple[int, ...],
    ms: tuple[int, ...],
    pitch: float,
    box: Rect,
) -> tuple[PerspectiveRay, ...]:
    chords: list[tuple[float, float, float, float]] = []
    for k in _every_second(ks):
        x = cx + (k + 0.5) * pitch
        chords.append((x, box.y, 2 * cx - x, box.bottom))
    for m in _every_second(ms):
        y = cy + (m + 0.5) * pitch
        chords.append((box.x, y, box.right, 2 * cy - y))
    chords.append((box.x, cy, box.right, cy))
    chords.append((cx, box.y, cx, box.bottom))
    chords.sort(key=lambda chord: _angle(*chord))
    rays: list[PerspectiveRay] = []
    for i, (x1, y1, x2, y2) in enumerate(chords):
        axis = _is_horizontal_axis(y1, y2, cy) or _is_vertical_axis(x1, x2, cx)
        rays.append(PerspectiveRay(x1, y1, x2, y2, dark=axis or i % 2 == 0))
    return tuple(rays)


def _angle(x1: float, y1: float, x2: float, y2: float) -> float:
    """Undirected direction in ``[0, π)``. 0 is +x; π/2 is +y (page down)."""
    theta = math.atan2(y2 - y1, x2 - x1)
    if theta < 0.0:
        theta += math.pi
    if theta >= math.pi - 1e-12:
        theta = 0.0
    return theta


def _is_horizontal_axis(y1: float, y2: float, cy: float) -> bool:
    return abs(y1 - cy) <= 1e-6 and abs(y2 - cy) <= 1e-6


def _is_vertical_axis(x1: float, x2: float, cx: float) -> bool:
    return abs(x1 - cx) <= 1e-6 and abs(x2 - cx) <= 1e-6
