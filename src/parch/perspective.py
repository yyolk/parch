"""Edge-to-edge perspective grid. Pad-only has no cover; a notebook may prefix one.

Square grid lines sit on the half-pitch lattice around the page center, so the
vanishing point is the center of a square and opposite edges share one fall-off:

    x = cx + (k + 1/2) · p
    y = cy + (k + 1/2) · p

Rays leave that center at equal angles ``θ = k · PERSPECTIVE_RAY_STEP_DEG``
(page y grows down). Even ``k`` is dark, odd ``k`` is light. Opposite rays are
one chord, so 72 rays are 36 chords through the vanishing point.
"""

import math
from dataclasses import dataclass

from parch.components.perspective import PerspectivePad
from parch.geom import Rect
from parch.sections.page import Page
from parch.spec import Spec

# This page only. Not a Spec/TOML knob, and not the engineering/dotgrid pitch.
PERSPECTIVE_PITCH_MM = 7.0
# Equal-angle fan. Not a Spec/TOML knob. 360 / 5 = 72 rays, 36 chords.
PERSPECTIVE_RAY_STEP_DEG = 5.0


@dataclass(frozen=True, slots=True)
class PerspectiveRay:
    """Ray from the vanishing point to the page edge at ``k`` steps."""

    x1: float
    y1: float
    x2: float
    y2: float
    k: int
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
    still meet the page. Rays are ``θ = k · PERSPECTIVE_RAY_STEP_DEG`` for
    ``k = 0 .. 360/step - 1``, each clipped from the page center to the edge.
    """
    cx = box.x + box.w / 2
    cy = box.y + box.h / 2
    ks = _indices(cx, box.x, box.right, pitch)
    ms = _indices(cy, box.y, box.bottom, pitch)
    verticals = tuple(cx + (k + 0.5) * pitch for k in ks)
    horizontals = tuple(cy + (m + 0.5) * pitch for m in ms)
    rays = _rays(cx, cy, box)
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


def _direction(k: int) -> tuple[float, float]:
    """Unit direction at ``k`` steps. 0° is +x; 90° is +y (page down)."""
    theta = math.radians(k * PERSPECTIVE_RAY_STEP_DEG)
    dx = math.cos(theta)
    dy = math.sin(theta)
    if abs(dx) < 1e-9:
        dx = 0.0
    if abs(dy) < 1e-9:
        dy = 0.0
    return dx, dy


def _rays(cx: float, cy: float, box: Rect) -> tuple[PerspectiveRay, ...]:
    count = int(round(360.0 / PERSPECTIVE_RAY_STEP_DEG))
    rays: list[PerspectiveRay] = []
    for k in range(count):
        dx, dy = _direction(k)
        x2, y2 = _clip_ray(cx, cy, dx, dy, box)
        rays.append(PerspectiveRay(cx, cy, x2, y2, k, dark=(k % 2 == 0)))
    return tuple(rays)


def _snap(value: float, lo: float, hi: float) -> float:
    if abs(value - lo) <= 1e-6:
        return lo
    if abs(value - hi) <= 1e-6:
        return hi
    return value


def _clip_ray(
    cx: float, cy: float, dx: float, dy: float, box: Rect
) -> tuple[float, float]:
    """First page-edge hit of the ray from ``(cx, cy)`` along ``(dx, dy)``."""
    hits: list[float] = []
    if dx > 0.0:
        hits.append((box.right - cx) / dx)
    elif dx < 0.0:
        hits.append((box.x - cx) / dx)
    if dy > 0.0:
        hits.append((box.bottom - cy) / dy)
    elif dy < 0.0:
        hits.append((box.y - cy) / dy)
    if not hits:
        raise ValueError("perspective ray has no direction")
    t = min(hits)
    return (
        _snap(cx + t * dx, box.x, box.right),
        _snap(cy + t * dy, box.y, box.bottom),
    )
