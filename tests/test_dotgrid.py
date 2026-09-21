from pathlib import Path

import pytest
from pypdf import PdfReader

from parch import ConfigError
from parch.components import DotGridPad
from parch.devices.registry import NAV_H, NOMAD, SCRIBE
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.painters import (
    CLONE_DOT,
    CLONE_DOT_PITCH,
    HEADER_H,
    RULE_C,
    paint_clone_dot_grid,
    paint_dot_grid_pad,
)
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.sections.dotgrid import DotGridPadSection
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


def _expected_dot_count(box) -> int:
    nx = max(2, int(box.w / CLONE_DOT_PITCH))
    ny = max(2, int(box.h / CLONE_DOT_PITCH))
    return nx * ny


def test_section_emits_one_page_per_sheet():
    spec = Spec(dotgrid_sheets=2)
    pages = DotGridPadSection(spec).pages()
    assert [page.kind for page in pages] == ["dot_grid", "dot_grid"]
    assert [page.dest for page in pages] == ["dotgrid-2026-01", "dotgrid-2026-02"]
    first = pages[0].components[0]
    assert isinstance(first, DotGridPad)
    assert first.sheet == 1
    assert first.sheets == 2
    assert pages[0].nav == ()
    assert pages[0].title == "Dot grid"


def test_section_empty_when_no_sheets():
    assert DotGridPadSection(Spec()).pages() == []


def test_spec_dotgrid_dests_and_toml():
    spec = Spec(dotgrid_sheets=1)
    assert spec.dest_for_dotgrid_pad(1) == "dotgrid-2026-01"
    example = Spec.from_path(Path("examples/dotgrid-pad.toml"))
    assert example.dotgrid_sheets == 1
    assert example.engineering_sheets == 0
    assert example.steno_sheets == 0
    assert example.device == "supernote-nomad"
    assert example.year == 2026
    assert example.book == "year-planner"
    assert "year =" not in Path("examples/dotgrid-pad.toml").read_text()
    assert Spec.from_mapping({"dotgrid": {"sheets": 2}}).dotgrid_sheets == 2
    assert Spec.from_mapping({"dotgrid": {}}).dotgrid_sheets == 0
    # DG1 leftover: a bare top-level int is not a table and is ignored.
    assert Spec.from_mapping({"dotgrid_sheets": 4}).dotgrid_sheets == 0
    with pytest.raises(ConfigError, match="dotgrid must be a TOML table"):
        Spec.from_mapping({"dotgrid": 4})
    with pytest.raises(ConfigError, match="unknown dotgrid key 'pitch'"):
        Spec.from_mapping({"dotgrid": {"sheets": 1, "pitch": 2.8}})
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


def test_paint_is_full_bleed_clone_pitch_without_chrome():
    pad = DotGridPad(sheet=1, sheets=1)
    ink = RecordingPlotter()
    paint_dot_grid_pad(ink, NOMAD, pad)
    texts = _texts(ink)
    assert texts == []
    assert "Subject" not in texts
    assert "Dot grid" not in texts
    page = NOMAD.page_rect()
    frame = NOMAD.content_frame()
    dots = _dots(ink)
    assert len(dots) == _expected_dot_count(page)
    assert all(op[5] == pytest.approx(RULE_C) for op in dots)
    xs = [op[1].x for op in dots]
    ys = [op[1].y for op in dots]
    rights = [op[1].right for op in dots]
    bottoms = [op[1].bottom for op in dots]
    assert min(xs) < NOMAD.writing_clearance
    assert max(rights) > NOMAD.page_width - NOMAD.writing_clearance
    assert min(ys) < NOMAD.top_clearance
    assert max(bottoms) > NOMAD.page_height - NAV_H
    assert min(xs) >= page.x - 1e-9
    assert max(rights) <= page.right + 1e-9
    assert min(ys) >= page.y - 1e-9
    assert max(bottoms) <= page.bottom + 1e-9
    frames = [
        op
        for op in ink.ops
        if op[0] == "rect" and op[1] == frame and op[2] and not op[3]
    ]
    assert not frames
    shared = RecordingPlotter()
    paint_clone_dot_grid(shared, page)
    assert len(_dots(shared)) == len(dots)


def test_paint_scribe_is_also_full_page():
    ink = RecordingPlotter()
    paint_dot_grid_pad(ink, SCRIBE, DotGridPad(sheet=1, sheets=1))
    page = SCRIBE.page_rect()
    dots = _dots(ink)
    assert len(dots) == _expected_dot_count(page)
    assert min(op[1].x for op in dots) < SCRIBE.writing_clearance
    assert max(op[1].bottom for op in dots) > SCRIBE.page_height - NAV_H


def test_layout_skips_planner_slab_and_nav():
    spec = Spec(dotgrid_sheets=1)
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
    assert spec.cover_dest not in dests
    page = reader.pages[0]
    assert float(page.mediabox.width) == pytest.approx(118.87 / 25.4 * 72.0, abs=0.6)
    assert float(page.mediabox.height) == pytest.approx(158.5 / 25.4 * 72.0, abs=0.6)
