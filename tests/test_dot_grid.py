from pathlib import Path

import pytest
from pypdf import PdfReader

from parch import ConfigError
from parch.components import DotGridPad
from parch.devices.registry import NOMAD, SCRIBE
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.painters import (
    CLONE_DOT,
    CLONE_DOT_PITCH,
    HEADER_H,
    RULE_C,
    SOFT,
    _paint_clone_dot_grid,
    device_page,
    paint_dot_grid,
    paint_dot_grid_pad,
)
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.sections.dot_grid import DotGridPadSection
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


def test_section_emits_one_page_per_sheet():
    spec = Spec(dot_sheets=2)
    pages = DotGridPadSection(spec).pages()
    assert [page.kind for page in pages] == ["dot_grid", "dot_grid"]
    assert [page.dest for page in pages] == ["dot-2026-01", "dot-2026-02"]
    first = pages[0].components[0]
    assert isinstance(first, DotGridPad)
    assert first.sheet == 1
    assert first.sheets == 2
    assert pages[0].nav == ()
    assert pages[0].title == "Dot grid"


def test_section_empty_when_no_sheets():
    assert DotGridPadSection(Spec()).pages() == []


def test_spec_dot_dests_and_toml():
    spec = Spec(dot_sheets=1)
    assert spec.dest_for_dot_pad(1) == "dot-2026-01"
    example = Spec.from_path(Path("examples/dot-grid-pad.toml"))
    assert example.dot_sheets == 2
    assert example.engineering_sheets == 0
    assert example.steno_sheets == 0
    assert example.device == "supernote-nomad"
    assert example.year == 2026
    assert "year =" not in Path("examples/dot-grid-pad.toml").read_text()
    assert Spec.from_mapping({"dot": {"sheets": 3}}).dot_sheets == 3
    with pytest.raises(ConfigError, match="dot_sheets must be 0–100"):
        Spec(dot_sheets=101)
    with pytest.raises(ConfigError, match="dot_sheets must be >= 1"):
        Spec().dest_for_dot_pad(1)
    with pytest.raises(ConfigError, match="dot sheet out of range"):
        spec.dest_for_dot_pad(2)
    both = Spec(dot_sheets=1, engineering_sheets=1, steno_sheets=1)
    assert both.dot_sheets == 1
    assert both.engineering_sheets == 1
    assert both.steno_sheets == 1


def test_clone_helper_is_shared_painter():
    box = Rect(10, 12, 40, 50)
    shared = RecordingPlotter()
    clone = RecordingPlotter()
    paint_dot_grid(shared, box)
    _paint_clone_dot_grid(clone, box)
    assert shared.ops == clone.ops
    assert CLONE_DOT_PITCH == pytest.approx(2.8)
    assert CLONE_DOT == pytest.approx(0.32)
    dots = _dots(shared)
    assert dots
    assert all(op[5] == pytest.approx(RULE_C) for op in dots)


def test_device_page_is_full_slate():
    for device in (NOMAD, SCRIBE):
        page = device_page(device)
        frame = device.content_frame()
        assert page == Rect(0.0, 0.0, device.page_width, device.page_height)
        assert page.x < frame.x
        assert page.y < frame.y
        assert page.right > frame.right
        assert page.bottom > frame.bottom


def test_paint_is_edge_to_edge_without_header():
    pad = DotGridPad(sheet=1, sheets=1)
    ink = RecordingPlotter()
    paint_dot_grid_pad(ink, NOMAD, pad)
    texts = _texts(ink)
    assert texts == []
    assert "Subject" not in texts
    assert "Dot grid" not in texts
    page = device_page(NOMAD)
    frame = NOMAD.content_frame()
    frames = [
        op
        for op in ink.ops
        if op[0] == "rect" and op[1] == page and op[2] and not op[3]
    ]
    assert frames
    assert frames[0][6] == pytest.approx(SOFT)
    content_frames = [
        op
        for op in ink.ops
        if op[0] == "rect" and op[1] == frame and op[2] and not op[3]
    ]
    assert not content_frames
    dots = _dots(ink)
    assert len(dots) > 100
    assert all(op[5] == pytest.approx(RULE_C) for op in dots)
    assert any(op[1].x < frame.x for op in dots)
    assert any(op[1].y < frame.y for op in dots)
    assert any(op[1].bottom > frame.bottom for op in dots)
    assert any(op[1].right > frame.right for op in dots)
    assert all(op[1].x >= page.x for op in dots)
    assert all(op[1].right <= page.right for op in dots)
    assert all(op[1].y >= page.y for op in dots)
    assert all(op[1].bottom <= page.bottom for op in dots)


def test_layout_skips_planner_slab_and_nav():
    spec = Spec(dot_sheets=1)
    page = DotGridPadSection(spec).pages()[0]
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
        and op[1].h == pytest.approx(HEADER_H)
    ]
    assert not top_fills


def test_press_example_toml_is_two_pages(tmp_path: Path):
    out = tmp_path / "dot-grid-pad.pdf"
    spec = Spec.from_path(Path("examples/dot-grid-pad.toml"))
    press(spec, out)
    reader = PdfReader(out)
    assert len(reader.pages) == 2
    dests = {str(key).lstrip("/") for key in (reader.named_destinations or {})}
    assert spec.dest_for_dot_pad(1) in dests
    assert spec.dest_for_dot_pad(2) in dests
    assert spec.year_dest not in dests
    assert spec.cover_dest not in dests
    page = reader.pages[0]
    assert float(page.mediabox.width) == pytest.approx(118.87 / 25.4 * 72.0, abs=0.6)
    assert float(page.mediabox.height) == pytest.approx(158.5 / 25.4 * 72.0, abs=0.6)
