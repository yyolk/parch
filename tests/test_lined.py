"""Lined pad: free-function lined_pages + press branch. Full-bleed notes ruling."""

from pathlib import Path

import pytest
from pypdf import PdfReader

from parch import ConfigError
from parch.components import LinedPad
from parch.devices.registry import NOMAD, SCRIBE
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.painters import (
    HEADER_H,
    LINE_PITCH,
    RULE,
    RULE_C,
    paint_lined_page,
    paint_lines,
)
from parch.lined import lined_pages
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.spec import Spec


def _texts(plotter: RecordingPlotter) -> list[str]:
    return [op[2] for op in plotter.text_ops()]


def _rules(plotter: RecordingPlotter) -> list[tuple]:
    return [
        op
        for op in plotter.ops
        if op[0] == "line"
        and op[5] == pytest.approx(RULE)
        and op[6] == pytest.approx(RULE_C)
        and op[2] == pytest.approx(op[4])
    ]


def test_lined_pages_emits_one_page_per_sheet():
    spec = Spec(lined_sheets=2)
    pages = lined_pages(spec)
    assert [page.kind for page in pages] == ["lined", "lined"]
    assert [page.dest for page in pages] == ["lined-2026-01", "lined-2026-02"]
    first = pages[0].components[0]
    assert isinstance(first, LinedPad)
    assert first.sheet == 1
    assert first.sheets == 2
    assert pages[0].nav == ()
    assert pages[0].title == "Lined"


def test_lined_pages_empty_when_no_sheets():
    assert lined_pages(Spec()) == []


def test_spec_lined_dests_and_toml():
    spec = Spec(lined_sheets=1)
    assert spec.dest_for_lined_pad(1) == "lined-2026-01"
    example = Spec.from_path(Path("examples/lined-pad.toml"))
    assert example.lined_sheets == 1
    assert example.engineering_sheets == 0
    assert example.steno_sheets == 0
    assert example.dotgrid_sheets == 0
    assert example.device == "supernote-nomad"
    assert example.year == 2026
    assert "year =" not in Path("examples/lined-pad.toml").read_text()
    assert Spec.from_mapping({"lined": {"sheets": 2}}).lined_sheets == 2
    with pytest.raises(ConfigError, match="lined_sheets must be 0–100"):
        Spec(lined_sheets=101)
    with pytest.raises(ConfigError, match="lined_sheets must be >= 1"):
        Spec().dest_for_lined_pad(1)
    with pytest.raises(ConfigError, match="lined sheet out of range"):
        spec.dest_for_lined_pad(2)


def test_paint_fills_page_rect_without_pocket_frame():
    pad = LinedPad(sheet=1, sheets=1)
    for device in (NOMAD, SCRIBE):
        ink = RecordingPlotter()
        paint_lined_page(ink, device, pad)
        page = device.page_rect()
        assert page == Rect(0.0, 0.0, device.page_width, device.page_height)
        expected = 0
        y = page.y + LINE_PITCH
        while y < page.bottom - 0.15:
            expected += 1
            y += LINE_PITCH
        rules = _rules(ink)
        assert len(rules) == expected
        assert all(op[1] == pytest.approx(page.x) for op in rules)
        assert all(op[3] == pytest.approx(page.right) for op in rules)
        ys = [op[2] for op in rules]
        assert min(ys) == pytest.approx(LINE_PITCH)
        assert max(ys) < page.bottom
        frames = [
            op
            for op in ink.ops
            if op[0] == "rect" and op[2] and not op[3] and op[1] == page
        ]
        assert not frames
        assert _texts(ink) == []


def test_paint_lines_is_the_shared_helper():
    box = Rect(0.0, 0.0, 28.0, 14.0)
    ink = RecordingPlotter()
    paint_lines(ink, box)
    expected = 0
    y = box.y + LINE_PITCH
    while y < box.bottom - 0.15:
        expected += 1
        y += LINE_PITCH
    assert len(_rules(ink)) == expected


def test_layout_skips_planner_slab_and_nav():
    spec = Spec(lined_sheets=1)
    page = lined_pages(spec)[0]
    ink = RecordingPlotter()
    PlannerLayout().paint(page, ink, NOMAD)
    texts = _texts(ink)
    assert "Year" not in texts
    assert "Quar" not in texts
    assert "Lined" not in texts
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
    ]
    assert not top_fills


def test_press_example_toml_is_one_page(tmp_path: Path):
    out = tmp_path / "lined-pad.pdf"
    spec = Spec.from_path(Path("examples/lined-pad.toml"))
    press(spec, out)
    reader = PdfReader(out)
    assert len(reader.pages) == 1
    dests = {str(key).lstrip("/") for key in (reader.named_destinations or {})}
    assert spec.dest_for_lined_pad(1) in dests
    assert spec.year_dest not in dests
    assert spec.cover_dest not in dests


@pytest.mark.parametrize(
    "kwargs",
    [
        {"engineering_sheets": 1},
        {"steno_sheets": 1},
        {"dotgrid_sheets": 1},
        {"perspective_sheets": 1},
        {"lined_dotgrid_sheets": 1},
        {"dotgrid_lined_sheets": 1},
        {"engineering_sheets": 1, "steno_sheets": 1, "dotgrid_sheets": 1},
    ],
)
def test_year_planner_rejects_lined_mixed_with_other_pads(kwargs):
    with pytest.raises(
        ConfigError, match="year-planner cannot mix lined_sheets with other pad counts"
    ):
        Spec(lined_sheets=1, **kwargs)
    with pytest.raises(
        ConfigError, match="year-planner cannot mix lined_sheets with other pad counts"
    ):
        Spec(book="year-planner", lined_sheets=1, **kwargs)
