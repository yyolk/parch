from pathlib import Path

import pytest
from pypdf import PdfReader

from parch import ConfigError
from parch.components import StenoPad
from parch.devices.registry import NOMAD, SCRIBE
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.painters import (
    HAIR,
    HEADER_H,
    MUTED,
    RULE,
    STENO_PITCH_MM,
    STENO_V_BOTTOM_MM,
    STENO_V_TOP_MM,
    StenoRuling,
    paint_steno_pad,
    steno_horizontal_field,
    steno_ruling,
)
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.sections.steno import StenoPadSection
from parch.spec import Spec


def _texts(plotter: RecordingPlotter) -> list[str]:
    return [op[2] for op in plotter.text_ops()]


def _lines(plotter: RecordingPlotter) -> list[tuple]:
    return [op for op in plotter.ops if op[0] == "line"]


def test_section_emits_one_page_per_sheet():
    spec = Spec(steno_sheets=2)
    pages = StenoPadSection(spec).pages()
    assert [page.kind for page in pages] == ["steno", "steno"]
    assert [page.dest for page in pages] == ["steno-2026-01", "steno-2026-02"]
    first = pages[0].components[0]
    assert isinstance(first, StenoPad)
    assert first.sheet == 1
    assert first.sheets == 2
    assert pages[0].nav == ()
    assert pages[0].title == "Steno"


def test_section_empty_when_no_sheets():
    assert StenoPadSection(Spec()).pages() == []


def test_spec_steno_dests_and_toml():
    spec = Spec(steno_sheets=1)
    assert spec.dest_for_steno_pad(1) == "steno-2026-01"
    example = Spec.from_path(Path("examples/steno-pad.toml"))
    assert example.steno_sheets == 1
    assert example.engineering_sheets == 0
    assert example.device == "supernote-nomad"
    assert example.year == 2026
    assert "year =" not in Path("examples/steno-pad.toml").read_text()
    assert Spec.from_mapping({"steno": {"sheets": 2}}).steno_sheets == 2
    with pytest.raises(ConfigError, match="steno_sheets must be 0–100"):
        Spec(steno_sheets=101)
    with pytest.raises(ConfigError, match="steno_sheets must be >= 1"):
        Spec().dest_for_steno_pad(1)
    with pytest.raises(ConfigError, match="steno sheet out of range"):
        spec.dest_for_steno_pad(2)
    both = Spec(steno_sheets=1, engineering_sheets=1)
    assert both.steno_sheets == 1
    assert both.engineering_sheets == 1


def test_ruling_is_gregg_pitch_with_equal_columns():
    assert STENO_PITCH_MM == pytest.approx(25.4 / 3)
    for device in (NOMAD, SCRIBE):
        frame = device.content_frame()
        ruling = steno_ruling(frame)
        assert isinstance(ruling, StenoRuling)
        assert ruling.pitch == pytest.approx(STENO_PITCH_MM)
        assert ruling.n_lines >= 2
        assert ruling.origin.y == pytest.approx(frame.y)
        assert ruling.origin.x == pytest.approx(frame.x)
        assert ruling.origin.w == pytest.approx(frame.w)
        assert ruling.origin.bottom <= frame.bottom + 1e-9
        assert ruling.origin.h == pytest.approx((ruling.n_lines - 1) * ruling.pitch)
        left = ruling.center_x - frame.x
        right = frame.right - ruling.center_x
        assert left == pytest.approx(right, abs=1e-6)
        leftover = frame.bottom - ruling.origin.bottom
        assert leftover >= -1e-9
        assert leftover < ruling.pitch


def test_paint_is_inset_center_without_frame():
    pad = StenoPad(sheet=1, sheets=1)
    for device in (NOMAD, SCRIBE):
        ink = RecordingPlotter()
        paint_steno_pad(ink, device, pad)
        assert _texts(ink) == []
        assert not [op for op in ink.ops if op[0] == "rect"]
        field = steno_horizontal_field(device)
        ruling = steno_ruling(field)
        horizontals = [
            op
            for op in _lines(ink)
            if op[2] == op[4]
            and op[5] == pytest.approx(RULE)
            and op[6] == pytest.approx(MUTED)
        ]
        centers = [
            op
            for op in _lines(ink)
            if op[1] == op[3]
            and op[5] == pytest.approx(HAIR)
            and op[6] == pytest.approx(MUTED)
        ]
        assert len(horizontals) == ruling.n_lines
        assert len(centers) == 1
        assert horizontals[0][1] == pytest.approx(field.x)
        assert horizontals[0][3] == pytest.approx(field.right)
        ys = sorted(op[2] for op in horizontals)
        assert ys[0] == pytest.approx(field.y)
        for prev, nxt in zip(ys, ys[1:]):
            assert nxt - prev == pytest.approx(STENO_PITCH_MM)
        center = centers[0]
        assert center[1] == pytest.approx(device.page_width / 2)
        assert center[2] == pytest.approx(STENO_V_TOP_MM)
        assert center[4] == pytest.approx(device.page_height - STENO_V_BOTTOM_MM)
        assert center[2] < ys[0]
        assert center[4] > ys[-1]


def test_layout_skips_planner_slab_and_nav():
    spec = Spec(steno_sheets=1)
    page = StenoPadSection(spec).pages()[0]
    ink = RecordingPlotter()
    PlannerLayout().paint(page, ink, NOMAD)
    texts = _texts(ink)
    assert "Year" not in texts
    assert "Quar" not in texts
    assert "Steno" not in texts
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
    out = tmp_path / "steno-pad.pdf"
    spec = Spec.from_path(Path("examples/steno-pad.toml"))
    press(spec, out)
    reader = PdfReader(out)
    assert len(reader.pages) == 1
    dests = {str(key).lstrip("/") for key in (reader.named_destinations or {})}
    assert spec.dest_for_steno_pad(1) in dests
    assert spec.year_dest not in dests
    page = reader.pages[0]
    assert float(page.mediabox.width) == pytest.approx(118.87 / 25.4 * 72.0, abs=0.6)
    assert float(page.mediabox.height) == pytest.approx(158.5 / 25.4 * 72.0, abs=0.6)
