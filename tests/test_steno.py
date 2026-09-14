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
    INK,
    paint_steno_pad,
    steno_ruling,
)
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.sections.steno import StenoPadSection
from parch.spec import (
    GREGG_LINE_PITCH_MM,
    STENO_PAGES_MAX,
    STENO_PITCH_MAX_MM,
    STENO_PITCH_MIN_MM,
    Spec,
    Steno,
)


def _texts(plotter: RecordingPlotter) -> list[str]:
    return [op[2] for op in plotter.text_ops()]


def _lines(plotter: RecordingPlotter) -> list[tuple]:
    return [op for op in plotter.ops if op[0] == "line"]


def _horizontals(plotter: RecordingPlotter) -> list[tuple]:
    return [op for op in _lines(plotter) if op[2] == op[4] and op[1] != op[3]]


def _verticals(plotter: RecordingPlotter) -> list[tuple]:
    return [op for op in _lines(plotter) if op[1] == op[3] and op[2] != op[4]]


def _close(a: float, b: float) -> bool:
    return abs(a - b) < 1e-6


def test_section_emits_one_page_per_sheet():
    spec = Spec(steno=Steno(pages=2))
    pages = StenoPadSection(spec).pages()
    assert [page.kind for page in pages] == ["steno", "steno"]
    assert [page.dest for page in pages] == ["steno-2026-01", "steno-2026-02"]
    first = pages[0].components[0]
    assert isinstance(first, StenoPad)
    assert first.sheet == 1
    assert first.sheets == 2
    assert first.line_pitch_mm == pytest.approx(GREGG_LINE_PITCH_MM)
    assert first.center_rule is True
    assert pages[0].nav == ()
    assert pages[1].components[0].sheet == 2


def test_section_empty_when_pages_zero():
    assert StenoPadSection(Spec()).pages() == []
    assert Spec().steno.pages == 0


def test_year_planner_walk_unchanged_when_pages_zero_or_opted():
    from parch.books import YearPlanner

    bare = {page.dest for page in YearPlanner().pages(Spec(notes_pages=1, months=(1,)))}
    zero = {
        page.dest
        for page in YearPlanner().pages(
            Spec(notes_pages=1, months=(1,), steno=Steno(pages=0))
        )
    }
    opted = {
        page.dest
        for page in YearPlanner().pages(
            Spec(notes_pages=1, months=(1,), steno=Steno(pages=3))
        )
    }
    assert bare == zero == opted
    assert not any(dest.startswith("steno-") for dest in bare)


def test_spec_steno_dests_and_closed_toml():
    spec = Spec(steno=Steno(pages=1))
    assert spec.dest_for_steno(1) == "steno-2026-01"
    example = Spec.from_path(Path("examples/steno.toml"))
    assert example.steno.pages == 1
    assert example.steno.line_pitch_mm == pytest.approx(GREGG_LINE_PITCH_MM)
    assert example.steno.center_rule is True
    assert example.device == "supernote-nomad"
    mapped = Spec.from_mapping(
        {"steno": {"pages": 4, "line_pitch_mm": 7.0, "center_rule": False}}
    )
    assert mapped.steno.pages == 4
    assert mapped.steno.line_pitch_mm == pytest.approx(7.0)
    assert mapped.steno.center_rule is False
    nomad = Spec.from_path(Path("examples/nomad.toml"))
    assert nomad.steno == Steno()
    assert nomad.steno.pages == 0
    with pytest.raises(ConfigError, match="steno.pages must be 0–"):
        Spec(steno=Steno(pages=STENO_PAGES_MAX + 1))
    with pytest.raises(ConfigError, match="steno.line_pitch_mm must be"):
        Spec(steno=Steno(line_pitch_mm=STENO_PITCH_MIN_MM - 0.1))
    with pytest.raises(ConfigError, match="steno.line_pitch_mm must be"):
        Spec(steno=Steno(line_pitch_mm=STENO_PITCH_MAX_MM + 0.1))
    with pytest.raises(ConfigError, match="unknown steno key 'holes'"):
        Spec.from_mapping({"steno": {"pages": 1, "holes": True}})
    with pytest.raises(ConfigError, match="unknown steno key 'duplex'"):
        Spec.from_mapping({"steno": {"duplex": False}})
    with pytest.raises(ConfigError, match="steno must be a TOML table"):
        Spec.from_mapping({"steno": "gregg"})
    with pytest.raises(ConfigError, match="steno.pages must be an int"):
        Spec.from_mapping({"steno": {"pages": 1.5}})
    with pytest.raises(ConfigError, match="steno.center_rule must be a bool"):
        Spec.from_mapping({"steno": {"center_rule": 1}})
    with pytest.raises(ConfigError, match="steno.pages must be >= 1"):
        Spec().dest_for_steno(1)
    with pytest.raises(ConfigError, match="steno sheet out of range"):
        spec.dest_for_steno(2)


def test_default_pitch_is_gregg_third_inch():
    assert GREGG_LINE_PITCH_MM == pytest.approx(25.4 / 3)
    assert 8.4 < GREGG_LINE_PITCH_MM < 8.5
    assert STENO_PITCH_MIN_MM <= GREGG_LINE_PITCH_MM <= STENO_PITCH_MAX_MM
    assert Steno().line_pitch_mm == pytest.approx(GREGG_LINE_PITCH_MM)
    assert Steno().center_rule is True


def test_knobs_change_horizontal_line_counts():
    frame = NOMAD.content_frame()
    default = steno_ruling(frame, GREGG_LINE_PITCH_MM, True)
    tight = steno_ruling(frame, 7.0, True)
    loose = steno_ruling(frame, 10.0, True)
    assert len(tight.ys) > len(default.ys) > len(loose.ys)
    ink_default = RecordingPlotter()
    paint_steno_pad(
        ink_default,
        NOMAD,
        StenoPad(GREGG_LINE_PITCH_MM, True, 1, 1),
    )
    ink_tight = RecordingPlotter()
    paint_steno_pad(ink_tight, NOMAD, StenoPad(7.0, True, 1, 1))
    ink_loose = RecordingPlotter()
    paint_steno_pad(ink_loose, NOMAD, StenoPad(10.0, True, 1, 1))
    assert len(_horizontals(ink_tight)) == len(tight.ys)
    assert len(_horizontals(ink_default)) == len(default.ys)
    assert len(_horizontals(ink_loose)) == len(loose.ys)
    assert len(_horizontals(ink_tight)) > len(_horizontals(ink_default))
    assert len(_horizontals(ink_default)) > len(_horizontals(ink_loose))
    scribe = steno_ruling(SCRIBE.content_frame(), GREGG_LINE_PITCH_MM, True)
    assert len(scribe.ys) > len(default.ys)


def test_center_rule_knob_toggles_midline():
    frame = NOMAD.content_frame()
    on = RecordingPlotter()
    paint_steno_pad(on, NOMAD, StenoPad(GREGG_LINE_PITCH_MM, True, 1, 1))
    off = RecordingPlotter()
    paint_steno_pad(off, NOMAD, StenoPad(GREGG_LINE_PITCH_MM, False, 1, 1))
    ruling = steno_ruling(frame, GREGG_LINE_PITCH_MM, True)
    cx = ruling.center_x
    assert cx is not None
    on_centers = [
        op for op in _verticals(on) if _close(op[1], cx) and _close(op[3], cx)
    ]
    off_centers = [
        op for op in _verticals(off) if _close(op[1], cx) and _close(op[3], cx)
    ]
    assert len(on_centers) == 1
    assert on_centers[0][2] == pytest.approx(ruling.origin.y)
    assert on_centers[0][4] == pytest.approx(ruling.origin.bottom)
    assert on_centers[0][5] == pytest.approx(HAIR)
    assert on_centers[0][6] == pytest.approx(INK)
    assert off_centers == []
    assert len(_horizontals(on)) == len(_horizontals(off))
    assert steno_ruling(frame, GREGG_LINE_PITCH_MM, False).center_x is None
    assert cx == pytest.approx(frame.x + frame.w / 2)


def test_ruling_stays_in_content_frame_without_header():
    pad = StenoPad(GREGG_LINE_PITCH_MM, True, 1, 1)
    ink = RecordingPlotter()
    paint_steno_pad(ink, NOMAD, pad)
    assert _texts(ink) == []
    frame = NOMAD.content_frame()
    ruling = steno_ruling(frame, GREGG_LINE_PITCH_MM, True)
    assert ruling.origin.h == pytest.approx((len(ruling.ys) + 1) * ruling.pitch)
    assert ruling.origin.bottom <= frame.bottom + 1e-6
    frames = [
        op
        for op in ink.ops
        if op[0] == "rect" and op[1] == ruling.origin and op[2] and not op[3]
    ]
    assert frames
    assert frames[0][4] == pytest.approx(HAIR)
    assert frames[0][6] == pytest.approx(INK)
    for op in _lines(ink):
        xs = (op[1], op[3])
        ys = (op[2], op[4])
        assert min(xs) >= frame.x - 1e-6
        assert max(xs) <= frame.right + 1e-6
        assert min(ys) >= frame.y - 1e-6
        assert max(ys) <= frame.bottom + 1e-6


def test_layout_skips_planner_slab_and_nav():
    spec = Spec(steno=Steno(pages=1))
    page = StenoPadSection(spec).pages()[0]
    ink = RecordingPlotter()
    PlannerLayout().paint(page, ink, NOMAD)
    texts = _texts(ink)
    assert texts == []
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
        and op[5] == pytest.approx(INK)
    ]
    assert not slabs


def test_press_example_toml_is_one_device_page(tmp_path: Path):
    out = tmp_path / "steno.pdf"
    spec = Spec.from_path(Path("examples/steno.toml"))
    press(spec, out)
    reader = PdfReader(out)
    assert len(reader.pages) == 1
    page = reader.pages[0]
    mm = 25.4
    assert float(page.mediabox.width) == pytest.approx(118.87 / mm * 72.0, abs=0.6)
    assert float(page.mediabox.height) == pytest.approx(158.5 / mm * 72.0, abs=0.6)
    dests = {str(key).lstrip("/") for key in (reader.named_destinations or {})}
    assert spec.dest_for_steno(1) in dests
    assert spec.year_dest not in dests
    assert "engineering-2026-01-front" not in dests
    multi = tmp_path / "steno-3.pdf"
    press(Spec(steno=Steno(pages=3)), multi)
    assert len(PdfReader(multi).pages) == 3
