"""Perspective pad: full-bleed square grid, centered vanishing point, clipped rays."""

import math
from pathlib import Path

import pytest
from pypdf import PdfReader

from parch import ConfigError
from parch.books import PerspectiveNotebook, book_for
from parch.components import CoverTitle, PerspectivePad
from parch.devices.registry import NOMAD, SCRIBE
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.painters import (
    ENG_PITCH_MM,
    GHOST,
    HAIR,
    HEADER_H,
    MUTED,
    RULE,
    RULE_C,
    PerspectiveGrid,
    paint_perspective_page,
    perspective_grid,
)
from parch.perspective import perspective_pages
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.spec import Spec


def _texts(plotter: RecordingPlotter) -> list[str]:
    return [op[2] for op in plotter.text_ops()]


def _lines(plotter: RecordingPlotter) -> list[tuple]:
    return [op for op in plotter.ops if op[0] == "line"]


def _on_boundary(page: Rect, x: float, y: float) -> bool:
    inside = page.x - 1e-6 <= x <= page.right + 1e-6
    inside = inside and page.y - 1e-6 <= y <= page.bottom + 1e-6
    on_edge = (
        abs(x - page.x) <= 1e-6
        or abs(x - page.right) <= 1e-6
        or abs(y - page.y) <= 1e-6
        or abs(y - page.bottom) <= 1e-6
    )
    return inside and on_edge


def _expected_ray_count(grid: PerspectiveGrid) -> int:
    """One ray per grid line, plus the two axes, plus the two page diagonals.

    A grid line that sits on an edge already produces the corner diagonal, so
    that diagonal is not an extra ray. When both axes land on grid lines the
    same diagonal is produced twice (once from each edge) and counts once.
    """
    page = grid.page
    vertical_on_edge = any(abs(x - page.x) <= 1e-6 for x in grid.verticals)
    horizontal_on_edge = any(abs(y - page.y) <= 1e-6 for y in grid.horizontals)
    if vertical_on_edge and horizontal_on_edge:
        return len(grid.verticals) + len(grid.horizontals)
    if vertical_on_edge or horizontal_on_edge:
        return len(grid.verticals) + len(grid.horizontals) + 2
    return len(grid.verticals) + len(grid.horizontals) + 4


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


def test_notebook_is_cover_then_perspective_pages():
    spec = Spec(book="perspective-notebook", perspective_sheets=2, title="Perspective")
    pages = PerspectiveNotebook().pages(spec)
    assert [page.kind for page in pages] == ["cover", "perspective", "perspective"]
    assert len(pages) == 1 + spec.perspective_sheets
    cover = pages[0].components[0]
    assert isinstance(cover, CoverTitle)
    assert cover.cta_dest == spec.dest_for_perspective_pad(1)
    assert cover.display_title == "Perspective"
    assert cover.specs_lead == ""
    assert pages[1].dest == spec.dest_for_perspective_pad(1)
    assert book_for("perspective-notebook") is PerspectiveNotebook


def test_press_selects_notebook_from_toml(tmp_path: Path):
    spec = Spec.from_path(Path("examples/perspective-notebook.toml"))
    assert spec.book == "perspective-notebook"
    assert spec.perspective_sheets == 12
    assert spec.outline is True
    out = tmp_path / "perspective-notebook.pdf"
    press(spec, out)
    reader = PdfReader(out)
    dests = {str(key).lstrip("/") for key in (reader.named_destinations or {})}
    assert spec.dest_for_perspective_pad(1) in dests
    assert spec.dest_for_perspective_pad(12) in dests
    assert spec.cover_dest in dests
    assert reader.outline == []
    assert len(reader.pages) == 1 + spec.perspective_sheets


@pytest.mark.parametrize(
    "page",
    [
        NOMAD.page_rect(),
        SCRIBE.page_rect(),
        Rect(0.0, 0.0, 100.0, 63.0),
        Rect(1.5, 2.25, 90.0, 130.4),
        Rect(0.0, 0.0, 55.0, 35.0),
    ],
)
def test_opposite_edges_share_falloff_and_center_is_a_cell(page: Rect):
    grid = perspective_grid(page, ENG_PITCH_MM)
    left, right, top, bottom = grid.falloff
    assert left == pytest.approx(right)
    assert top == pytest.approx(bottom)
    assert 0.0 <= left < ENG_PITCH_MM
    assert 0.0 <= top < ENG_PITCH_MM
    cx, cy = grid.center
    assert cx == pytest.approx(page.x + page.w / 2)
    assert cy == pytest.approx(page.y + page.h / 2)
    assert grid.verticals
    assert grid.horizontals
    assert min(abs(x - cx) for x in grid.verticals) == pytest.approx(ENG_PITCH_MM / 2)
    assert min(abs(y - cy) for y in grid.horizontals) == pytest.approx(ENG_PITCH_MM / 2)
    assert cx - ENG_PITCH_MM / 2 == pytest.approx(
        min(grid.verticals, key=lambda x: abs(x - (cx - ENG_PITCH_MM / 2)))
    )
    visible_left = grid.verticals[0] - page.x
    visible_right = page.right - grid.verticals[-1]
    assert visible_left == pytest.approx(visible_right)
    visible_top = grid.horizontals[0] - page.y
    visible_bottom = page.bottom - grid.horizontals[-1]
    assert visible_top == pytest.approx(visible_bottom)
    assert left == pytest.approx(
        0.0 if visible_left <= 1e-6 else ENG_PITCH_MM - visible_left
    )
    assert top == pytest.approx(
        0.0 if visible_top <= 1e-6 else ENG_PITCH_MM - visible_top
    )


def test_zero_falloff_puts_a_grid_line_on_each_edge():
    page = Rect(0.0, 0.0, 55.0, 55.0)
    grid = perspective_grid(page, 5.0)
    assert grid.falloff == pytest.approx((0.0, 0.0, 0.0, 0.0))
    assert grid.verticals[0] == pytest.approx(0.0)
    assert grid.verticals[-1] == pytest.approx(55.0)
    assert grid.horizontals[0] == pytest.approx(0.0)
    assert grid.horizontals[-1] == pytest.approx(55.0)
    assert len(grid.rays) == _expected_ray_count(grid)
    wide = perspective_grid(Rect(0.0, 0.0, 55.0, 40.0), 5.0)
    assert wide.falloff[0] == pytest.approx(0.0)
    assert wide.falloff[2] > 0.0
    assert len(wide.rays) == _expected_ray_count(wide)


def test_rays_alternate_and_are_clipped_to_the_page():
    for page in (NOMAD.page_rect(), SCRIBE.page_rect(), Rect(0.0, 0.0, 100.0, 63.0)):
        grid = perspective_grid(page, ENG_PITCH_MM)
        cx, cy = grid.center
        assert len(grid.rays) == _expected_ray_count(grid)
        assert len(grid.rays) >= 2
        angles = [ray.angle for ray in grid.rays]
        assert angles == sorted(angles)
        assert all(angles[i] < angles[i + 1] for i in range(len(angles) - 1))
        assert all(0.0 <= ray.angle < math.pi for ray in grid.rays)
        for index, ray in enumerate(grid.rays):
            assert ray.gray == pytest.approx(MUTED if index % 2 == 0 else GHOST)
            assert _on_boundary(page, ray.x1, ray.y1)
            assert _on_boundary(page, ray.x2, ray.y2)
            assert (ray.x1 + ray.x2) / 2 == pytest.approx(cx)
            assert (ray.y1 + ray.y2) / 2 == pytest.approx(cy)


def test_vanishing_point_is_the_page_center_not_the_content_frame():
    page = SCRIBE.page_rect()
    frame = SCRIBE.content_frame()
    grid = perspective_grid(page, ENG_PITCH_MM)
    cx, cy = grid.center
    assert cx == pytest.approx(page.w / 2)
    assert cy == pytest.approx(page.h / 2)
    assert cy != pytest.approx(frame.y + frame.h / 2)
    assert grid.verticals[0] < frame.x
    assert grid.horizontals[0] == pytest.approx(page.y, abs=ENG_PITCH_MM)


def test_paint_covers_the_physical_page_without_a_frame():
    pad = PerspectivePad(sheet=1, sheets=1)
    for device in (NOMAD, SCRIBE):
        ink = RecordingPlotter()
        paint_perspective_page(ink, device, pad)
        page = device.page_rect()
        grid = perspective_grid(page, ENG_PITCH_MM)
        lines = _lines(ink)
        grid_lines = [
            op
            for op in lines
            if op[5] == pytest.approx(RULE) and op[6] == pytest.approx(RULE_C)
        ]
        rays = [
            op
            for op in lines
            if op[5] == pytest.approx(HAIR)
            and op[6] in (pytest.approx(MUTED), pytest.approx(GHOST))
        ]
        assert len(grid_lines) == len(grid.verticals) + len(grid.horizontals)
        assert len(rays) == len(grid.rays)
        verticals = [op for op in grid_lines if op[1] == pytest.approx(op[3])]
        horizontals = [op for op in grid_lines if op[2] == pytest.approx(op[4])]
        assert len(verticals) == len(grid.verticals)
        assert len(horizontals) == len(grid.horizontals)
        assert all(op[2] == pytest.approx(0.0) for op in verticals)
        assert all(op[4] == pytest.approx(device.page_height) for op in verticals)
        assert all(op[1] == pytest.approx(0.0) for op in horizontals)
        assert all(op[3] == pytest.approx(device.page_width) for op in horizontals)
        assert min(op[2] for op in horizontals) < device.top_clearance + ENG_PITCH_MM
        assert min(op[1] for op in verticals) < device.writing_clearance
        frames = [op for op in ink.ops if op[0] == "rect"]
        assert frames == []
        assert _texts(ink) == []
        assert rays[0][6] == pytest.approx(MUTED)
        assert rays[1][6] == pytest.approx(GHOST)


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
    assert _lines(ink)


def test_press_example_toml_is_one_page(tmp_path: Path):
    out = tmp_path / "perspective-pad.pdf"
    spec = Spec.from_path(Path("examples/perspective-pad.toml"))
    press(spec, out)
    reader = PdfReader(out)
    assert len(reader.pages) == 1
    assert reader.outline == []
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
        match="cannot mix perspective_sheets|cannot mix lined_sheets|cannot mix duplex",
    ):
        Spec(perspective_sheets=1, **kwargs)


def test_perspective_notebook_rejects_other_pad_counts():
    with pytest.raises(
        ConfigError, match="perspective-notebook requires perspective_sheets >= 1"
    ):
        Spec(book="perspective-notebook")
    with pytest.raises(
        ConfigError, match="perspective-notebook cannot set engineering_sheets"
    ):
        Spec(book="perspective-notebook", perspective_sheets=1, engineering_sheets=1)
    with pytest.raises(
        ConfigError, match="perspective-notebook cannot set dotgrid_sheets"
    ):
        Spec(book="perspective-notebook", perspective_sheets=1, dotgrid_sheets=1)
    with pytest.raises(
        ConfigError, match="perspective-notebook cannot set lined_sheets"
    ):
        Spec(book="perspective-notebook", perspective_sheets=1, lined_sheets=1)
    with pytest.raises(
        ConfigError, match="perspective-notebook cannot set lined_dotgrid_sheets"
    ):
        Spec(
            book="perspective-notebook",
            perspective_sheets=1,
            lined_dotgrid_sheets=1,
        )
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
