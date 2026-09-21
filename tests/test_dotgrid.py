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
    device_page_rect,
    dot_grid_counts,
    paint_dot_grid,
    paint_dot_grid_page,
)
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.sections.dotgrid import DotGridSection
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
    spec = Spec(dotgrid_sheets=2)
    pages = DotGridSection(spec).pages()
    assert [page.kind for page in pages] == ["dotgrid", "dotgrid"]
    assert [page.dest for page in pages] == ["dotgrid-2026-01", "dotgrid-2026-02"]
    first = pages[0].components[0]
    assert isinstance(first, DotGridPad)
    assert first.sheet == 1
    assert first.sheets == 2
    assert pages[0].nav == ()
    assert pages[0].title == "Dot grid"


def test_section_empty_when_no_sheets():
    assert DotGridSection(Spec()).pages() == []


def test_spec_dotgrid_dests_and_toml():
    spec = Spec(dotgrid_sheets=1)
    assert spec.dest_for_dotgrid_pad(1) == "dotgrid-2026-01"
    example = Spec.from_path(Path("examples/dotgrid-pad.toml"))
    assert example.dotgrid_sheets == 1
    assert example.engineering_sheets == 0
    assert example.steno_sheets == 0
    assert example.device == "supernote-nomad"
    assert example.year == 2026
    assert "year =" not in Path("examples/dotgrid-pad.toml").read_text()
    assert Spec.from_mapping({"dotgrid": {"sheets": 2}}).dotgrid_sheets == 2
    with pytest.raises(ConfigError, match="dotgrid_sheets must be 0–100"):
        Spec(dotgrid_sheets=101)
    with pytest.raises(ConfigError, match="dotgrid_sheets must be >= 1"):
        Spec().dest_for_dotgrid_pad(1)
    with pytest.raises(ConfigError, match="dotgrid sheet out of range"):
        spec.dest_for_dotgrid_pad(2)
    both = Spec(dotgrid_sheets=1, steno_sheets=1, engineering_sheets=1)
    assert both.dotgrid_sheets == 1
    assert both.steno_sheets == 1
    assert both.engineering_sheets == 1


def test_page_rect_is_device_bounds_without_clearance():
    for device in (NOMAD, SCRIBE):
        page = device_page_rect(device)
        assert page == Rect(0.0, 0.0, device.page_width, device.page_height)
        frame = device.content_frame()
        assert page.x < frame.x
        assert page.y < frame.y or device.top_clearance == 0
        assert page.right > frame.right
        assert page.bottom > frame.bottom
        assert page.x == pytest.approx(0.0)
        assert page.y == pytest.approx(0.0)
        assert page.w == pytest.approx(device.page_width)
        assert page.h == pytest.approx(device.page_height)


def test_paint_is_full_bleed_dots_without_header():
    pad = DotGridPad(sheet=1, sheets=1)
    ink = RecordingPlotter()
    paint_dot_grid_page(ink, NOMAD, pad)
    texts = _texts(ink)
    assert texts == []
    page = device_page_rect(NOMAD)
    nx, ny = dot_grid_counts(page)
    dots = _dots(ink)
    assert (nx, ny) == (
        max(2, int(NOMAD.page_width / CLONE_DOT_PITCH)),
        max(2, int(NOMAD.page_height / CLONE_DOT_PITCH)),
    )
    assert len(dots) == nx * ny
    assert all(op[5] == pytest.approx(RULE_C) for op in dots)
    xs = [op[1].x for op in dots]
    ys = [op[1].y for op in dots]
    assert min(xs) >= page.x - 1e-9
    assert min(ys) >= page.y - 1e-9
    assert max(op[1].right for op in dots) <= page.right + 1e-9
    assert max(op[1].bottom for op in dots) <= page.bottom + 1e-9
    # Edge-to-edge: first/last dots sit in the page-bound cells, not writing_clearance.
    assert min(xs) < NOMAD.writing_clearance
    assert min(ys) < NOMAD.top_clearance
    frames = [op for op in ink.ops if op[0] == "rect" and op[2] and not op[3]]
    assert frames == []


def test_shared_paint_matches_clone_pitch():
    box = Rect(10.0, 12.0, 40.0, 28.0)
    ink = RecordingPlotter()
    paint_dot_grid(ink, box)
    nx, ny = dot_grid_counts(box)
    dots = _dots(ink)
    assert len(dots) == nx * ny
    assert all(op[1].w == pytest.approx(CLONE_DOT) for op in dots)
    assert CLONE_DOT_PITCH == pytest.approx(2.8)


def test_layout_skips_planner_slab_and_nav():
    spec = Spec(dotgrid_sheets=1)
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
        and op[1].h == pytest.approx(NOMAD.top_clearance + HEADER_H)
    ]
    assert not top_fills


def test_press_example_toml_is_one_page(tmp_path: Path):
    out = tmp_path / "dotgrid-pad.pdf"
    spec = Spec.from_path(Path("examples/dotgrid-pad.toml"))
    press(spec, out)
    reader = PdfReader(out)
    assert len(reader.pages) == 1
    dests = {str(key).lstrip("/") for key in (reader.named_destinations or {})}
    assert spec.dest_for_dotgrid_pad(1) in dests
    assert spec.year_dest not in dests
    page = reader.pages[0]
    assert float(page.mediabox.width) == pytest.approx(118.87 / 25.4 * 72.0, abs=0.6)
    assert float(page.mediabox.height) == pytest.approx(158.5 / 25.4 * 72.0, abs=0.6)
