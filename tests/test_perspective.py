"""Perspective pad: full-bleed square grid, center-cell vanishing point."""

import math
from pathlib import Path

import pytest
from pypdf import PdfReader

from parch import ConfigError
from parch.components import PerspectivePad
from parch.devices import get_device
from parch.devices.registry import NOMAD, SCRIBE, known_device_ids
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.painters import (
    GHOST,
    HEADER_H,
    MUTED,
    PERSPECTIVE_PITCH_MM,
    RULE,
    RULE_C,
    paint_perspective_page,
    perspective_grid,
    perspective_rays,
)
from parch.perspective import perspective_pages
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.spec import Spec


def _texts(plotter: RecordingPlotter) -> list[str]:
    return [op[2] for op in plotter.text_ops()]


def _lines(plotter: RecordingPlotter) -> list[tuple]:
    return [op for op in plotter.ops if op[0] == "line"]


def _expected_falloff(length: float, pitch: float) -> float:
    """Partial square when lines sit at center ± pitch/2 + k·pitch."""
    half = length / 2
    steps = math.floor((half - pitch / 2) / pitch)
    return half - (pitch / 2 + steps * pitch)


def _on_boundary(x: float, y: float, page: Rect) -> bool:
    on_edge = (
        x == pytest.approx(page.x)
        or x == pytest.approx(page.right)
        or y == pytest.approx(page.y)
        or y == pytest.approx(page.bottom)
    )
    inside = page.x <= x <= page.right and page.y <= y <= page.bottom
    return bool(on_edge and inside)


@pytest.mark.parametrize("device_id", known_device_ids())
def test_falloff_is_symmetric_on_each_device(device_id: str):
    device = get_device(device_id)
    page = device.page_rect()
    grid = perspective_grid(page)
    assert PERSPECTIVE_PITCH_MM == 10.0
    assert grid.pitch == PERSPECTIVE_PITCH_MM
    assert grid.cx == pytest.approx(page.w / 2)
    assert grid.cy == pytest.approx(page.h / 2)
    assert grid.falloff_left == pytest.approx(grid.falloff_right)
    assert grid.falloff_top == pytest.approx(grid.falloff_bottom)
    assert grid.falloff_left == pytest.approx(_expected_falloff(page.w, grid.pitch))
    assert grid.falloff_top == pytest.approx(_expected_falloff(page.h, grid.pitch))
    assert 0 <= grid.falloff_left < grid.pitch
    assert 0 <= grid.falloff_top < grid.pitch
    assert grid.verticals[0] - page.x == pytest.approx(grid.falloff_left)
    assert page.right - grid.verticals[-1] == pytest.approx(grid.falloff_right)
    assert grid.horizontals[0] - page.y == pytest.approx(grid.falloff_top)
    assert page.bottom - grid.horizontals[-1] == pytest.approx(grid.falloff_bottom)


@pytest.mark.parametrize("device", (NOMAD, SCRIBE))
def test_vanishing_point_is_the_center_of_a_square(device):
    page = device.page_rect()
    grid = perspective_grid(page)
    left = max(x for x in grid.verticals if x < grid.cx)
    right = min(x for x in grid.verticals if x > grid.cx)
    above = max(y for y in grid.horizontals if y < grid.cy)
    below = min(y for y in grid.horizontals if y > grid.cy)
    assert right - left == pytest.approx(grid.pitch)
    assert below - above == pytest.approx(grid.pitch)
    assert grid.cx - left == pytest.approx(grid.pitch / 2)
    assert right - grid.cx == pytest.approx(grid.pitch / 2)
    assert grid.cy - above == pytest.approx(grid.pitch / 2)
    assert below - grid.cy == pytest.approx(grid.pitch / 2)
    assert all(x != pytest.approx(grid.cx) for x in grid.verticals)
    assert all(y != pytest.approx(grid.cy) for y in grid.horizontals)


def test_small_page_matches_half_step_lines():
    page = Rect(0.0, 0.0, 23.0, 17.0)
    grid = perspective_grid(page, pitch=5.0)
    assert grid.verticals == pytest.approx((4.0, 9.0, 14.0, 19.0))
    assert grid.horizontals == pytest.approx((1.0, 6.0, 11.0, 16.0))
    assert grid.falloff_left == pytest.approx(4.0)
    assert grid.falloff_right == pytest.approx(4.0)
    assert grid.falloff_top == pytest.approx(1.0)
    assert grid.falloff_bottom == pytest.approx(1.0)


def _undirected_angle(ray) -> float:
    """Line orientation in ``[0, π)``. Opposite directions share one angle."""
    angle = math.atan2(ray.y2 - ray.y1, ray.x2 - ray.x1)
    if angle < 0:
        angle += math.pi
    if angle >= math.pi:
        angle -= math.pi
    return angle


def _is_horizontal_axis(ray, grid, page: Rect) -> bool:
    return (
        ray.y1 == pytest.approx(grid.cy)
        and ray.y2 == pytest.approx(grid.cy)
        and {round(ray.x1, 5), round(ray.x2, 5)}
        == {round(page.x, 5), round(page.right, 5)}
    )


def _is_vertical_axis(ray, grid, page: Rect) -> bool:
    return (
        ray.x1 == pytest.approx(grid.cx)
        and ray.x2 == pytest.approx(grid.cx)
        and {round(ray.y1, 5), round(ray.y2, 5)}
        == {round(page.y, 5), round(page.bottom, 5)}
    )


def _is_axis(ray, grid, page: Rect) -> bool:
    return _is_horizontal_axis(ray, grid, page) or _is_vertical_axis(ray, grid, page)


def _is_edge_crossing(x: float, y: float, grid, page: Rect) -> bool:
    """A grid line meeting the page edge. Corners count only when a line lands there."""
    on_vertical = any(x == pytest.approx(vx) for vx in grid.verticals) and (
        y == pytest.approx(page.y) or y == pytest.approx(page.bottom)
    )
    on_horizontal = any(y == pytest.approx(hy) for hy in grid.horizontals) and (
        x == pytest.approx(page.x) or x == pytest.approx(page.right)
    )
    return bool(on_vertical or on_horizontal)


@pytest.mark.parametrize("device_id", known_device_ids())
def test_rays_cross_every_grid_edge_meeting(device_id: str):
    page = get_device(device_id).page_rect()
    grid = perspective_grid(page)
    rays = perspective_rays(page)
    # One chord per grid line (each line's two edge meetings pair with the
    # mirrored line) plus the horizontal and vertical axes through the center.
    assert len(rays) == len(grid.verticals) + len(grid.horizontals) + 2
    angles = [_undirected_angle(ray) for ray in rays]
    assert angles == sorted(angles)
    assert all(b > a for a, b in zip(angles, angles[1:], strict=False))
    axes = [ray for ray in rays if _is_axis(ray, grid, page)]
    assert len(axes) == 2
    assert all(ray.gray == MUTED for ray in axes)
    assert _is_horizontal_axis(rays[0], grid, page)
    assert _undirected_angle(rays[0]) == pytest.approx(0.0)
    verticals = [ray for ray in rays if _is_vertical_axis(ray, grid, page)]
    assert len(verticals) == 1
    assert _undirected_angle(verticals[0]) == pytest.approx(math.pi / 2)
    non_axis = [ray for ray in rays if not _is_axis(ray, grid, page)]
    assert [ray.gray for ray in non_axis] == [
        GHOST if i % 2 == 0 else MUTED for i in range(len(non_axis))
    ]
    corners = {
        (page.x, page.y),
        (page.right, page.y),
        (page.x, page.bottom),
        (page.right, page.bottom),
    }
    for ray in rays:
        assert (ray.x1 + ray.x2) / 2 == pytest.approx(grid.cx)
        assert (ray.y1 + ray.y2) / 2 == pytest.approx(grid.cy)
        assert _on_boundary(ray.x1, ray.y1, page)
        assert _on_boundary(ray.x2, ray.y2, page)
        for x, y in ((ray.x1, ray.y1), (ray.x2, ray.y2)):
            on_corner = any(
                x == pytest.approx(cx) and y == pytest.approx(cy) for cx, cy in corners
            )
            if on_corner:
                assert _is_edge_crossing(x, y, grid, page)
    for ray in non_axis:
        assert _is_edge_crossing(ray.x1, ray.y1, grid, page)
        assert _is_edge_crossing(ray.x2, ray.y2, grid, page)
    assert all(x != pytest.approx(grid.cx) for x in grid.verticals)
    assert all(y != pytest.approx(grid.cy) for y in grid.horizontals)


@pytest.mark.parametrize("device", (NOMAD, SCRIBE))
def test_paint_is_full_bleed_without_frame_or_header(device):
    pad = PerspectivePad(sheet=1, sheets=1)
    ink = RecordingPlotter()
    paint_perspective_page(ink, device, pad)
    page = device.page_rect()
    grid = perspective_grid(page)
    rays = perspective_rays(page)
    assert [op for op in ink.ops if op[0] == "rect"] == []
    assert _texts(ink) == []
    lines = _lines(ink)
    assert len(lines) == len(grid.verticals) + len(grid.horizontals) + len(rays)
    grid_lines = [op for op in lines if op[6] == pytest.approx(RULE_C)]
    ray_lines = [op for op in lines if op[6] != pytest.approx(RULE_C)]
    assert len(grid_lines) == len(grid.verticals) + len(grid.horizontals)
    assert len(ray_lines) == len(rays)
    assert all(op[5] == pytest.approx(RULE) for op in lines)
    assert {op[6] for op in ray_lines} == {MUTED, GHOST}
    assert any(
        op[2] == pytest.approx(0.0) and op[4] == pytest.approx(device.page_height)
        for op in grid_lines
    )
    assert any(
        op[1] == pytest.approx(0.0) and op[3] == pytest.approx(device.page_width)
        for op in grid_lines
    )
    assert min(min(op[1], op[3]) for op in lines) == pytest.approx(0.0)
    assert max(max(op[1], op[3]) for op in lines) == pytest.approx(device.page_width)
    assert min(min(op[2], op[4]) for op in lines) == pytest.approx(0.0)
    assert max(max(op[2], op[4]) for op in lines) == pytest.approx(device.page_height)
    if device.top_clearance:
        assert grid.falloff_top != pytest.approx(device.top_clearance)
        assert grid.horizontals[0] < device.content_top


def test_layout_skips_planner_slab_and_nav():
    page = perspective_pages(Spec(perspective_sheets=1))[0]
    assert page.kind == "perspective"
    relabeled = page.__class__(
        dest=page.dest,
        kind="not-a-literal",
        title=page.title,
        nav=page.nav,
        components=page.components,
    )
    ink = RecordingPlotter()
    PlannerLayout().paint(relabeled, ink, NOMAD)
    assert "Year" not in _texts(ink)
    assert "Perspective" not in _texts(ink)
    assert [op for op in ink.ops if op[0] == "rect"] == []
    slabs = [
        op
        for op in ink.ops
        if op[0] == "rect" and op[3] and op[1].h == pytest.approx(HEADER_H)
    ]
    assert not slabs
    assert _lines(ink)


def test_perspective_pages_emits_one_page_per_sheet():
    spec = Spec(perspective_sheets=2)
    pages = perspective_pages(spec)
    assert [page.kind for page in pages] == ["perspective", "perspective"]
    assert [page.dest for page in pages] == [
        "perspective-2026-01",
        "perspective-2026-02",
    ]
    first = pages[0].components[0]
    assert isinstance(first, PerspectivePad)
    assert first.sheet == 1
    assert first.sheets == 2
    assert pages[0].nav == ()
    assert pages[0].title == "Perspective"


def test_perspective_pages_empty_when_no_sheets():
    assert perspective_pages(Spec()) == []


def test_spec_perspective_dests_and_toml():
    spec = Spec(perspective_sheets=1)
    assert spec.dest_for_perspective_pad(1) == "perspective-2026-01"
    example = Spec.from_path(Path("examples/perspective-pad.toml"))
    assert example.perspective_sheets == 1
    assert example.engineering_sheets == 0
    assert example.steno_sheets == 0
    assert example.dotgrid_sheets == 0
    assert example.lined_sheets == 0
    assert example.device == "supernote-nomad"
    assert example.year == 2026
    assert "year =" not in Path("examples/perspective-pad.toml").read_text()
    assert Spec.from_mapping({"perspective": {"sheets": 2}}).perspective_sheets == 2
    with pytest.raises(ConfigError, match="perspective_sheets must be 0–100"):
        Spec(perspective_sheets=101)
    with pytest.raises(ConfigError, match="perspective_sheets must be >= 1"):
        Spec().dest_for_perspective_pad(1)
    with pytest.raises(ConfigError, match="perspective sheet out of range"):
        spec.dest_for_perspective_pad(2)


def test_press_example_toml_is_one_page(tmp_path: Path):
    out = tmp_path / "perspective-pad.pdf"
    spec = Spec.from_path(Path("examples/perspective-pad.toml"))
    press(spec, out)
    reader = PdfReader(out)
    assert len(reader.pages) == 1
    dests = {str(key).lstrip("/") for key in (reader.named_destinations or {})}
    assert spec.dest_for_perspective_pad(1) in dests
    assert spec.year_dest not in dests
    assert spec.cover_dest not in dests
    assert reader.outline == []


def test_press_with_outline_still_skips_the_pad(tmp_path: Path):
    spec = Spec(perspective_sheets=1, outline=True)
    plotter = RecordingPlotter()
    press(spec, tmp_path / "perspective.pdf", plotter=plotter)
    assert plotter.outlines() == []
    assert plotter.dests() == [spec.dest_for_perspective_pad(1)]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"engineering_sheets": 1},
        {"steno_sheets": 1},
        {"dotgrid_sheets": 1},
        {"lined_sheets": 1},
        {"lined_dotgrid_sheets": 1},
        {"dotgrid_lined_sheets": 1},
    ],
)
def test_year_planner_rejects_perspective_mixed_with_other_pads(kwargs):
    with pytest.raises(
        ConfigError,
        match="year-planner cannot mix .* with other pad counts",
    ):
        Spec(perspective_sheets=1, **kwargs)


def test_other_notebooks_reject_perspective_sheets():
    with pytest.raises(
        ConfigError, match="engineering-notebook cannot set perspective_sheets"
    ):
        Spec(book="engineering-notebook", engineering_sheets=1, perspective_sheets=1)
    with pytest.raises(
        ConfigError, match="dotgrid-notebook cannot set perspective_sheets"
    ):
        Spec(book="dotgrid-notebook", dotgrid_sheets=1, perspective_sheets=1)
    with pytest.raises(
        ConfigError, match="lined-notebook cannot set perspective_sheets"
    ):
        Spec(book="lined-notebook", lined_sheets=1, perspective_sheets=1)
    with pytest.raises(
        ConfigError, match="lined-dotgrid-mix-notebook cannot set perspective_sheets"
    ):
        Spec(
            book="lined-dotgrid-mix-notebook",
            lined_dotgrid_sheets=1,
            perspective_sheets=1,
        )
    with pytest.raises(
        ConfigError, match="perspective-notebook cannot set engineering_sheets"
    ):
        Spec(book="perspective-notebook", perspective_sheets=1, engineering_sheets=1)
    with pytest.raises(
        ConfigError, match="perspective-notebook cannot set lined_dotgrid_sheets"
    ):
        Spec(
            book="perspective-notebook",
            perspective_sheets=1,
            lined_dotgrid_sheets=1,
        )
    with pytest.raises(ConfigError, match="perspective-notebook requires"):
        Spec(book="perspective-notebook")
