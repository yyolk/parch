"""Full-bleed perspective grid: symmetric squares, center VP, grid-locked rays."""

import math
from pathlib import Path

import pytest
from pypdf import PdfReader

from parch import ConfigError
from parch.components import PerspectivePad
from parch.devices import get_device, known_device_ids
from parch.devices.registry import NOMAD, SCRIBE
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.painters import (
    GHOST,
    HAIR,
    HEADER_H,
    MUTED,
    RULE,
    RULE_C,
    paint_perspective_page,
)
from parch.perspective import (
    PERSPECTIVE_PITCH_MM,
    perspective_falloff,
    perspective_mesh,
    perspective_pages,
)
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.spec import Spec


def _texts(plotter: RecordingPlotter) -> list[str]:
    return [op[2] for op in plotter.text_ops()]


def _lines(plotter: RecordingPlotter) -> list[tuple]:
    return [op for op in plotter.ops if op[0] == "line"]


def _chord_angle(ray) -> float:
    theta = math.degrees(math.atan2(ray.y2 - ray.y1, ray.x2 - ray.x1))
    if theta < 0.0:
        theta += 180.0
    if theta >= 180.0 - 1e-9:
        theta = 0.0
    return theta


def _endpoints(ray) -> tuple[tuple[float, float], tuple[float, float]]:
    return tuple(
        sorted(
            ((round(ray.x1, 4), round(ray.y1, 4)), (round(ray.x2, 4), round(ray.y2, 4)))
        )
    )


def _reflect_x(ray, cx: float):
    return type(ray)(2 * cx - ray.x1, ray.y1, 2 * cx - ray.x2, ray.y2, ray.dark)


def _reflect_y(ray, cy: float):
    return type(ray)(ray.x1, 2 * cy - ray.y1, ray.x2, 2 * cy - ray.y2, ray.dark)


def _crossings(ray, mesh, page: Rect) -> int:
    found = 0
    for x, y in ((ray.x1, ray.y1), (ray.x2, ray.y2)):
        on_tb = y == pytest.approx(page.y) or y == pytest.approx(page.bottom)
        on_lr = x == pytest.approx(page.x) or x == pytest.approx(page.right)
        on_v = any(x == pytest.approx(vx) for vx in mesh.verticals)
        on_h = any(y == pytest.approx(hy) for hy in mesh.horizontals)
        if (on_tb and on_v) or (on_lr and on_h):
            found += 1
    return found


def _on_boundary(x: float, y: float, box: Rect) -> bool:
    on_x = x == pytest.approx(box.x) or x == pytest.approx(box.right)
    on_y = y == pytest.approx(box.y) or y == pytest.approx(box.bottom)
    inside = (
        box.x - 1e-6 <= x <= box.right + 1e-6 and box.y - 1e-6 <= y <= box.bottom + 1e-6
    )
    return inside and (on_x or on_y)


def _inside(x: float, y: float, box: Rect) -> bool:
    return (
        box.x - 1e-6 <= x <= box.right + 1e-6 and box.y - 1e-6 <= y <= box.bottom + 1e-6
    )


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
    example = Spec.from_path(Path("examples/perspective.toml"))
    assert example.perspective_sheets == 1
    assert example.engineering_sheets == 0
    assert example.steno_sheets == 0
    assert example.dotgrid_sheets == 0
    assert example.lined_sheets == 0
    assert example.device == "supernote-nomad"
    assert example.year == 2026
    assert "year =" not in Path("examples/perspective.toml").read_text()
    assert Spec.from_mapping({"perspective": {"sheets": 2}}).perspective_sheets == 2
    with pytest.raises(ConfigError, match="perspective_sheets must be 0–100"):
        Spec(perspective_sheets=101)
    with pytest.raises(ConfigError, match="perspective_sheets must be >= 1"):
        Spec().dest_for_perspective_pad(1)
    with pytest.raises(ConfigError, match="perspective sheet out of range"):
        spec.dest_for_perspective_pad(2)


@pytest.mark.parametrize("device_id", known_device_ids())
def test_grid_is_symmetric_and_vp_is_the_center_of_a_square(device_id: str):
    device = get_device(device_id)
    page = device.page_rect()
    mesh = perspective_mesh(page)
    assert PERSPECTIVE_PITCH_MM == 7.0
    assert page == Rect(0.0, 0.0, device.page_width, device.page_height)
    assert mesh.cx == pytest.approx(page.w / 2)
    assert mesh.cy == pytest.approx(page.h / 2)
    assert mesh.pitch == pytest.approx(PERSPECTIVE_PITCH_MM)
    left, right, top, bottom = perspective_falloff(mesh, page)
    assert left == pytest.approx(right)
    assert top == pytest.approx(bottom)
    assert 0.0 <= left < PERSPECTIVE_PITCH_MM
    assert 0.0 <= top < PERSPECTIVE_PITCH_MM
    assert all(abs(x - mesh.cx) > 1e-6 for x in mesh.verticals)
    assert all(abs(y - mesh.cy) > 1e-6 for y in mesh.horizontals)
    left_line = max(x for x in mesh.verticals if x < mesh.cx)
    right_line = min(x for x in mesh.verticals if x > mesh.cx)
    above = max(y for y in mesh.horizontals if y < mesh.cy)
    below = min(y for y in mesh.horizontals if y > mesh.cy)
    assert right_line - left_line == pytest.approx(PERSPECTIVE_PITCH_MM)
    assert below - above == pytest.approx(PERSPECTIVE_PITCH_MM)
    assert (left_line + right_line) / 2 == pytest.approx(mesh.cx)
    assert (above + below) / 2 == pytest.approx(mesh.cy)
    frame = device.content_frame()
    outside = any(x < frame.x or x > frame.right for x in mesh.verticals) or any(
        y < frame.y or y > frame.bottom for y in mesh.horizontals
    )
    assert outside


def test_falloff_mm_on_each_profile():
    nomad = perspective_mesh(NOMAD.page_rect())
    scribe = perspective_mesh(SCRIBE.page_rect())
    assert perspective_falloff(nomad, NOMAD.page_rect()) == pytest.approx(
        (6.935, 6.935, 5.75, 5.75)
    )
    assert perspective_falloff(scribe, SCRIBE.page_rect()) == pytest.approx(
        (5.24, 5.24, 3.485, 3.485)
    )


def test_ray_count_per_profile():
    assert len(perspective_mesh(NOMAD.page_rect()).rays) == 22
    assert len(perspective_mesh(SCRIBE.page_rect()).rays) == 30


@pytest.mark.parametrize("device_id", known_device_ids())
def test_rays_lock_to_every_second_crossing(device_id: str):
    device = get_device(device_id)
    page = device.page_rect()
    mesh = perspective_mesh(page)
    angles = [_chord_angle(ray) for ray in mesh.rays]
    assert angles == sorted(angles)
    horizontal = next(
        ray
        for ray in mesh.rays
        if ray.y1 == pytest.approx(mesh.cy) and ray.y2 == pytest.approx(mesh.cy)
    )
    vertical = next(
        ray
        for ray in mesh.rays
        if ray.x1 == pytest.approx(mesh.cx) and ray.x2 == pytest.approx(mesh.cx)
    )
    assert horizontal.dark is True
    assert vertical.dark is True
    assert _chord_angle(horizontal) == pytest.approx(0.0)
    assert _chord_angle(vertical) == pytest.approx(90.0)
    vertical_at = mesh.rays.index(vertical)
    for i, (a, b) in enumerate(zip(mesh.rays, mesh.rays[1:], strict=False)):
        if i in {vertical_at - 1, vertical_at}:
            assert a.dark and b.dark
        else:
            assert a.dark != b.dark
    assert mesh.rays[-1].dark != horizontal.dark
    keys = {_endpoints(ray) for ray in mesh.rays}
    for ray in mesh.rays:
        assert _endpoints(_reflect_x(ray, mesh.cx)) in keys
        assert _endpoints(_reflect_y(ray, mesh.cy)) in keys
        assert _on_boundary(ray.x1, ray.y1, page)
        assert _on_boundary(ray.x2, ray.y2, page)
        assert (ray.x1 + ray.x2) / 2 == pytest.approx(mesh.cx)
        assert (ray.y1 + ray.y2) / 2 == pytest.approx(mesh.cy)
        if ray is horizontal or ray is vertical:
            continue
        assert _crossings(ray, mesh, page) == 2
        for x, _y in ((ray.x1, ray.y1), (ray.x2, ray.y2)):
            on_vertical = any(x == pytest.approx(vx) for vx in mesh.verticals)
            on_horizontal = any(_y == pytest.approx(hy) for hy in mesh.horizontals)
            if on_vertical:
                half = round((x - mesh.cx) / (mesh.pitch / 2))
                assert abs(half) % 4 == 1
            if on_horizontal:
                half = round((_y - mesh.cy) / (mesh.pitch / 2))
                assert abs(half) % 4 == 1


def test_paint_is_full_bleed_without_frame_or_header():
    pad = PerspectivePad(sheet=1, sheets=1)
    for device in (NOMAD, SCRIBE):
        ink = RecordingPlotter()
        paint_perspective_page(ink, device, pad)
        page = device.page_rect()
        mesh = perspective_mesh(page)
        assert not [op for op in ink.ops if op[0] == "rect"]
        assert _texts(ink) == []
        lines = _lines(ink)
        verticals = [
            op
            for op in lines
            if op[1] == pytest.approx(op[3])
            and op[2] == pytest.approx(0.0)
            and op[4] == pytest.approx(device.page_height)
            and op[6] == pytest.approx(RULE_C)
        ]
        horizontals = [
            op
            for op in lines
            if op[2] == pytest.approx(op[4])
            and op[1] == pytest.approx(0.0)
            and op[3] == pytest.approx(device.page_width)
            and op[6] == pytest.approx(RULE_C)
        ]
        assert len(verticals) == len(mesh.verticals)
        assert len(horizontals) == len(mesh.horizontals)
        assert all(op[5] == pytest.approx(RULE) for op in verticals + horizontals)
        rays = [op for op in lines if op[6] != pytest.approx(RULE_C)]
        assert len(rays) == len(mesh.rays)
        assert all(
            op[6] == pytest.approx(MUTED) or op[6] == pytest.approx(GHOST)
            for op in rays
        )
        dark = [op for op in rays if op[6] == pytest.approx(MUTED)]
        light = [op for op in rays if op[6] == pytest.approx(GHOST)]
        assert len(dark) == sum(ray.dark for ray in mesh.rays)
        assert len(light) == sum(not ray.dark for ray in mesh.rays)
        assert all(op[5] == pytest.approx(HAIR) for op in dark)
        assert all(op[5] == pytest.approx(RULE) for op in light)
        frame = device.content_frame()
        assert any(op[2] < frame.y or op[2] > frame.bottom for op in horizontals)


def test_scribe_top_clearance_does_not_inset_the_grid():
    device = get_device("kindle-scribe", top_clearance=8.0)
    ink = RecordingPlotter()
    paint_perspective_page(ink, device, PerspectivePad(sheet=1, sheets=1))
    horizontals = [
        op[2]
        for op in _lines(ink)
        if op[2] == pytest.approx(op[4]) and op[6] == pytest.approx(RULE_C)
    ]
    assert min(horizontals) < device.content_top
    assert min(horizontals) == pytest.approx(3.485)


def test_layout_skips_planner_slab_and_nav():
    page = perspective_pages(Spec(perspective_sheets=1))[0]
    ink = RecordingPlotter()
    PlannerLayout().paint(page, ink, NOMAD)
    texts = _texts(ink)
    assert "Year" not in texts
    assert "Quar" not in texts
    assert "Perspective" not in texts
    slabs = [
        op
        for op in ink.ops
        if op[0] == "rect"
        and op[3]
        and op[1].y == pytest.approx(NOMAD.content_top)
        and op[1].h == pytest.approx(HEADER_H)
    ]
    assert not slabs


def test_press_example_toml_is_one_page(tmp_path: Path):
    out = tmp_path / "perspective.pdf"
    spec = Spec.from_path(Path("examples/perspective.toml"))
    press(spec, out)
    reader = PdfReader(out)
    assert len(reader.pages) == 1
    dests = {str(key).lstrip("/") for key in (reader.named_destinations or {})}
    assert spec.dest_for_perspective_pad(1) in dests
    assert spec.year_dest not in dests
    assert spec.cover_dest not in dests


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
