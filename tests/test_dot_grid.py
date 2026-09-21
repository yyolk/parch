from pathlib import Path

import pytest
from pypdf import PdfReader

from parch import ConfigError
from parch.components import DotGrid
from parch.devices.registry import NOMAD, SCRIBE
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.painters import (
    CLONE_DOT,
    CLONE_DOT_PITCH,
    HAIR,
    HEADER_H,
    RULE_C,
    SOFT,
    paint_dot_grid,
)
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.sections.dot_grid import DotGridSection
from parch.spec import Spec
from parch.tracks import columns, rows


def _texts(plotter: RecordingPlotter) -> list[str]:
    return [op[2] for op in plotter.text_ops()]


def _clone_dots(plotter: RecordingPlotter) -> list[Rect]:
    return [
        op[1]
        for op in plotter.ops
        if op[0] == "rect"
        and op[3]
        and not op[2]
        and op[1].w == pytest.approx(CLONE_DOT)
        and op[1].h == pytest.approx(CLONE_DOT)
        and op[5] == pytest.approx(RULE_C)
    ]


def _expected_dots(box: Rect) -> list[Rect]:
    nx = max(2, int(box.w / CLONE_DOT_PITCH))
    ny = max(2, int(box.h / CLONE_DOT_PITCH))
    return [
        Rect(
            cell.x + (cell.w - CLONE_DOT) / 2,
            cell.y + (cell.h - CLONE_DOT) / 2,
            CLONE_DOT,
            CLONE_DOT,
        )
        for band in rows(box, ny)
        for cell in columns(band, nx)
    ]


def test_section_emits_one_page_per_sheet():
    spec = Spec(dot_grid_sheets=2)
    pages = DotGridSection(spec).pages()
    assert [page.kind for page in pages] == ["dot_grid", "dot_grid"]
    assert [page.dest for page in pages] == ["dot-grid-2026-01", "dot-grid-2026-02"]
    first = pages[0].components[0]
    assert isinstance(first, DotGrid)
    assert first.sheet == 1
    assert first.sheets == 2
    assert pages[0].nav == ()
    assert pages[0].title == "Dot grid"


def test_section_empty_when_no_sheets():
    assert DotGridSection(Spec()).pages() == []


def test_spec_dot_grid_dests_and_toml():
    spec = Spec(dot_grid_sheets=1)
    assert spec.dest_for_dot_grid(1) == "dot-grid-2026-01"
    example = Spec.from_path(Path("examples/dot-grid.toml"))
    assert example.dot_grid_sheets == 1
    assert example.engineering_sheets == 0
    assert example.steno_sheets == 0
    assert example.device == "supernote-nomad"
    assert example.year == 2026
    assert "year =" not in Path("examples/dot-grid.toml").read_text()
    assert "CLONE_DOT_PITCH" in Path("examples/dot-grid.toml").read_text()
    assert Spec.from_mapping({"dot_grid": {"sheets": 2}}).dot_grid_sheets == 2
    with pytest.raises(ConfigError, match="dot_grid_sheets must be 0–100"):
        Spec(dot_grid_sheets=101)
    with pytest.raises(ConfigError, match="dot_grid_sheets must be >= 1"):
        Spec().dest_for_dot_grid(1)
    with pytest.raises(ConfigError, match="dot-grid sheet out of range"):
        spec.dest_for_dot_grid(2)
    with pytest.raises(
        ConfigError, match="engineering-notebook cannot set dot_grid_sheets"
    ):
        Spec(book="engineering-notebook", engineering_sheets=1, dot_grid_sheets=1)


def test_page_bleed_is_full_page_not_content_frame():
    for device in (NOMAD, SCRIBE):
        bleed = device.page_bleed()
        frame = device.content_frame()
        assert bleed == Rect(0.0, 0.0, device.page_width, device.page_height)
        assert bleed.x < frame.x
        assert bleed.y < frame.y
        assert bleed.right > frame.right
        assert bleed.bottom > frame.bottom


def test_paint_bleeds_clone_pitch_under_bezel():
    """Dots use project-note pitch and sit under clearance, not just content_frame."""
    assert CLONE_DOT_PITCH == pytest.approx(2.8)
    grid = DotGrid(sheet=1, sheets=1)
    for device in (NOMAD, SCRIBE):
        ink = RecordingPlotter()
        paint_dot_grid(ink, device, grid)
        bleed = device.page_bleed()
        frame = device.content_frame()
        expected = _expected_dots(bleed)
        dots = _clone_dots(ink)
        assert dots == expected
        assert len(dots) > 100
        assert any(dot.y < frame.y for dot in dots)
        assert any(dot.x < frame.x for dot in dots)
        assert any(dot.bottom > frame.bottom for dot in dots)
        assert any(dot.right > frame.right for dot in dots)
        frames = [
            op
            for op in ink.ops
            if op[0] == "rect" and op[1] == frame and op[2] and not op[3]
        ]
        assert not frames
        pockets = [
            op
            for op in ink.ops
            if op[0] == "rect"
            and op[2]
            and not op[3]
            and op[4] == pytest.approx(HAIR)
            and op[6] == pytest.approx(SOFT)
        ]
        assert not pockets
        assert _texts(ink) == []


def test_layout_skips_planner_slab_and_nav():
    spec = Spec(dot_grid_sheets=1)
    page = DotGridSection(spec).pages()[0]
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
    out = tmp_path / "dot-grid.pdf"
    spec = Spec.from_path(Path("examples/dot-grid.toml"))
    press(spec, out)
    reader = PdfReader(out)
    assert len(reader.pages) == 1
    dests = {str(key).lstrip("/") for key in (reader.named_destinations or {})}
    assert spec.dest_for_dot_grid(1) in dests
    assert spec.year_dest not in dests
    page = reader.pages[0]
    assert float(page.mediabox.width) == pytest.approx(118.87 / 25.4 * 72.0, abs=0.6)
    assert float(page.mediabox.height) == pytest.approx(158.5 / 25.4 * 72.0, abs=0.6)
