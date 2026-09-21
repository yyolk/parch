"""DG5: free-function dotgrid_pages + press branch. Full-bleed clone dots."""

from pathlib import Path

import pytest
from pypdf import PdfReader

from parch import ConfigError
from parch.components import DotGridPad
from parch.devices.registry import NOMAD, SCRIBE
from parch.dotgrid import dotgrid_pages
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.painters import (
    CLONE_DOT,
    CLONE_DOT_PITCH,
    HEADER_H,
    RULE_C,
    paint_dot_grid,
    paint_dotgrid_page,
)
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.spec import Spec


def _texts(plotter: RecordingPlotter) -> list[str]:
    return [op[2] for op in plotter.text_ops()]


def _dots(plotter: RecordingPlotter) -> list[tuple]:
    return [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[3]
        and not op[2]
        and op[1].w == pytest.approx(CLONE_DOT)
        and op[1].h == pytest.approx(CLONE_DOT)
    ]


def test_dotgrid_pages_emits_one_page_per_sheet():
    spec = Spec(dotgrid_sheets=2)
    pages = dotgrid_pages(spec)
    assert [page.kind for page in pages] == ["pad", "pad"]
    assert [page.dest for page in pages] == ["dotgrid-2026-01", "dotgrid-2026-02"]
    first = pages[0].components[0]
    assert isinstance(first, DotGridPad)
    assert first.sheet == 1
    assert first.sheets == 2
    assert pages[0].nav == ()
    assert pages[0].title == "Dot grid"


def test_dotgrid_pages_empty_when_no_sheets():
    assert dotgrid_pages(Spec()) == []


def test_spec_dotgrid_dests_and_toml():
    spec = Spec(dotgrid_sheets=1)
    assert spec.dest_for_dotgrid_pad(1) == "dotgrid-2026-01"
    example = Spec.from_path(Path("examples/dotgrid.toml"))
    assert example.dotgrid_sheets == 1
    assert example.engineering_sheets == 0
    assert example.steno_sheets == 0
    assert example.device == "supernote-nomad"
    assert example.year == 2026
    assert "year =" not in Path("examples/dotgrid.toml").read_text()
    assert Spec.from_mapping({"dotgrid": {"sheets": 2}}).dotgrid_sheets == 2
    with pytest.raises(ConfigError, match="dotgrid_sheets must be 0–100"):
        Spec(dotgrid_sheets=101)
    with pytest.raises(ConfigError, match="dotgrid_sheets must be >= 1"):
        Spec().dest_for_dotgrid_pad(1)
    with pytest.raises(ConfigError, match="dotgrid sheet out of range"):
        spec.dest_for_dotgrid_pad(2)
    both = Spec(dotgrid_sheets=1, engineering_sheets=1, steno_sheets=1)
    assert both.dotgrid_sheets == 1
    assert both.engineering_sheets == 1
    assert both.steno_sheets == 1


def test_paint_fills_page_rect_without_pocket_frame():
    pad = DotGridPad(sheet=1, sheets=1)
    for device in (NOMAD, SCRIBE):
        ink = RecordingPlotter()
        paint_dotgrid_page(ink, device, pad)
        page = device.page_rect()
        assert page == Rect(0.0, 0.0, device.page_width, device.page_height)
        nx = max(2, int(page.w / CLONE_DOT_PITCH))
        ny = max(2, int(page.h / CLONE_DOT_PITCH))
        dots = _dots(ink)
        assert len(dots) == nx * ny
        assert all(op[5] == pytest.approx(RULE_C) for op in dots)
        xs = [op[1].x for op in dots]
        ys = [op[1].y for op in dots]
        assert min(xs) < CLONE_DOT_PITCH
        assert page.right - (max(xs) + CLONE_DOT) < CLONE_DOT_PITCH
        assert min(ys) < CLONE_DOT_PITCH
        assert page.bottom - (max(ys) + CLONE_DOT) < CLONE_DOT_PITCH
        frames = [
            op
            for op in ink.ops
            if op[0] == "rect" and op[2] and not op[3] and op[1] == page
        ]
        assert not frames
        assert _texts(ink) == []


def test_paint_dot_grid_is_the_shared_helper():
    box = Rect(0.0, 0.0, 28.0, 14.0)
    ink = RecordingPlotter()
    paint_dot_grid(ink, box)
    nx = max(2, int(box.w / CLONE_DOT_PITCH))
    ny = max(2, int(box.h / CLONE_DOT_PITCH))
    assert len(_dots(ink)) == nx * ny


def test_layout_skips_planner_slab_and_nav():
    spec = Spec(dotgrid_sheets=1)
    page = dotgrid_pages(spec)[0]
    ink = RecordingPlotter()
    PlannerLayout().paint(page, ink, NOMAD)
    texts = _texts(ink)
    assert "Year" not in texts
    assert "Quar" not in texts
    assert "Dot grid" not in texts
    slabs = [
        op
        for op in ink.ops
        if op[0] == "rect"
        and op[3]
        and op[1].y == pytest.approx(NOMAD.content_top)
        and op[1].h == pytest.approx(HEADER_H)
        and op[5] == pytest.approx(0.0)
    ]
    assert not slabs
    top_fills = [
        op
        for op in ink.ops
        if op[0] == "rect"
        and op[3]
        and op[1].y == pytest.approx(0.0)
        and op[1].w == pytest.approx(NOMAD.page_width)
        and op[1].h != pytest.approx(CLONE_DOT)
    ]
    assert not top_fills


def test_press_example_toml_is_one_page(tmp_path: Path):
    out = tmp_path / "dotgrid.pdf"
    spec = Spec.from_path(Path("examples/dotgrid.toml"))
    press(spec, out)
    reader = PdfReader(out)
    assert len(reader.pages) == 1
    dests = {str(key).lstrip("/") for key in (reader.named_destinations or {})}
    assert spec.dest_for_dotgrid_pad(1) in dests
    assert spec.year_dest not in dests
    assert spec.cover_dest not in dests


def test_press_composes_engineering_steno_then_dotgrid(tmp_path: Path):
    spec = Spec(engineering_sheets=1, steno_sheets=1, dotgrid_sheets=1)
    plotter = RecordingPlotter()
    press(spec, tmp_path / "pads.pdf", plotter=plotter)
    assert plotter.dests() == [
        spec.dest_for_engineering_pad(1, "front"),
        spec.dest_for_engineering_pad(1, "back"),
        spec.dest_for_steno_pad(1),
        spec.dest_for_dotgrid_pad(1),
    ]
    assert spec.cover_dest not in plotter.dests()
    assert spec.year_dest not in plotter.dests()
