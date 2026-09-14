from pathlib import Path

import pytest
from pypdf import PdfReader

from parch import ConfigError
from parch.components import GreggPad
from parch.devices.registry import NOMAD, SCRIBE
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.painters import (
    GREGG_CENTER_W,
    GREGG_PITCH_MM,
    HAIR,
    HEADER_H,
    INK,
    RULE,
    RULE_C,
    gregg_gaps,
    gregg_pitch,
    paint_gregg_pad,
)
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.sections.gregg import GreggPadSection
from parch.spec import Spec


def _texts(plotter: RecordingPlotter) -> list[str]:
    return [op[2] for op in plotter.text_ops()]


def _lines(plotter: RecordingPlotter) -> list[tuple]:
    return [op for op in plotter.ops if op[0] == "line"]


def test_section_emits_one_page_per_sheet():
    spec = Spec(gregg_pages=2)
    pages = GreggPadSection(spec).pages()
    assert [page.kind for page in pages] == ["gregg", "gregg"]
    assert [page.dest for page in pages] == ["gregg-2026-01", "gregg-2026-02"]
    first = pages[0].components[0]
    assert isinstance(first, GreggPad)
    assert first.page == 1
    assert pages[1].components[0].page == 2
    assert pages[0].nav == ()


def test_section_empty_when_no_pages():
    assert GreggPadSection(Spec()).pages() == []


def test_spec_gregg_dests_and_toml():
    spec = Spec(gregg_pages=1)
    assert spec.dest_for_gregg_pad(1) == "gregg-2026-01"
    example = Spec.from_path(Path("examples/gregg-pad.toml"))
    assert example.gregg_pages == 1
    assert example.device == "supernote-nomad"
    scribe = Spec.from_path(Path("examples/gregg-pad-scribe.toml"))
    assert scribe.gregg_pages == 1
    assert scribe.device == "kindle-scribe"
    assert Spec.from_mapping({"gregg": {"pages": 2}}).gregg_pages == 2
    with pytest.raises(ConfigError, match="gregg_pages must be 0–24"):
        Spec(gregg_pages=25)
    with pytest.raises(ConfigError, match="gregg_pages must be >= 1"):
        Spec().dest_for_gregg_pad(1)
    with pytest.raises(ConfigError, match="gregg page out of range"):
        spec.dest_for_gregg_pad(2)


def test_pitch_snaps_to_content_frame_on_nomad_and_scribe():
    for device in (NOMAD, SCRIBE):
        frame = device.content_frame()
        n = gregg_gaps(frame.h)
        pitch = gregg_pitch(frame)
        assert n == max(1, round(frame.h / GREGG_PITCH_MM))
        assert pitch == pytest.approx(frame.h / n)
        assert pitch == pytest.approx(GREGG_PITCH_MM, rel=0.08)
        ink = RecordingPlotter()
        paint_gregg_pad(ink, device, GreggPad(page=1))
        horizontals = [
            op for op in _lines(ink) if op[2] == op[4] and op[5] == pytest.approx(RULE)
        ]
        assert len(horizontals) == n - 1
        ys = sorted(op[2] for op in horizontals)
        assert ys[0] == pytest.approx(frame.y + pitch)
        assert ys[-1] == pytest.approx(frame.bottom - pitch)
        for y0, y1 in zip(ys, ys[1:], strict=False):
            assert y1 - y0 == pytest.approx(pitch)
        assert all(op[1] == pytest.approx(frame.x) for op in horizontals)
        assert all(op[3] == pytest.approx(frame.right) for op in horizontals)
        assert all(op[6] == pytest.approx(RULE_C) for op in horizontals)


def test_center_spine_is_mid_x_and_heavier():
    for device in (NOMAD, SCRIBE):
        frame = device.content_frame()
        ink = RecordingPlotter()
        paint_gregg_pad(ink, device, GreggPad(page=1))
        mid = frame.x + frame.w / 2
        spines = [
            op
            for op in _lines(ink)
            if op[1] == op[3] and op[5] == pytest.approx(GREGG_CENTER_W)
        ]
        assert len(spines) == 1
        spine = spines[0]
        assert spine[1] == pytest.approx(mid)
        assert spine[2] == pytest.approx(frame.y)
        assert spine[4] == pytest.approx(frame.bottom)
        assert spine[6] == pytest.approx(INK)
        assert GREGG_CENTER_W > RULE
        assert GREGG_CENTER_W > HAIR


def test_ruling_stays_in_content_frame_without_text():
    ink = RecordingPlotter()
    paint_gregg_pad(ink, NOMAD, GreggPad(page=1))
    frame = NOMAD.content_frame()
    assert _texts(ink) == []
    frames = [
        op
        for op in ink.ops
        if op[0] == "rect" and op[1] == frame and op[2] and not op[3]
    ]
    assert frames
    assert frames[0][6] == pytest.approx(RULE_C)
    for op in _lines(ink):
        assert min(op[1], op[3]) >= frame.x - 1e-9
        assert max(op[1], op[3]) <= frame.right + 1e-9
        assert min(op[2], op[4]) >= frame.y - 1e-9
        assert max(op[2], op[4]) <= frame.bottom + 1e-9


def test_layout_skips_planner_slab_and_nav():
    spec = Spec(gregg_pages=1)
    page = GreggPadSection(spec).pages()[0]
    ink = RecordingPlotter()
    PlannerLayout().paint(page, ink, NOMAD)
    texts = _texts(ink)
    assert texts == []
    assert "Year" not in texts
    assert "Quar" not in texts
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
    out = tmp_path / "gregg-pad.pdf"
    spec = Spec.from_path(Path("examples/gregg-pad.toml"))
    press(spec, out)
    reader = PdfReader(out)
    assert len(reader.pages) == 1
    dests = {str(key).lstrip("/") for key in (reader.named_destinations or {})}
    assert spec.dest_for_gregg_pad(1) in dests
    assert spec.year_dest not in dests
    page = reader.pages[0]
    mm = 25.4
    assert float(page.mediabox.width) == pytest.approx(
        NOMAD.page_width / mm * 72, abs=0.6
    )
    assert float(page.mediabox.height) == pytest.approx(
        NOMAD.page_height / mm * 72, abs=0.6
    )


def test_press_scribe_example_is_one_scribe_page(tmp_path: Path):
    out = tmp_path / "gregg-pad-scribe.pdf"
    spec = Spec.from_path(Path("examples/gregg-pad-scribe.toml"))
    press(spec, out)
    reader = PdfReader(out)
    assert len(reader.pages) == 1
    page = reader.pages[0]
    mm = 25.4
    assert float(page.mediabox.width) == pytest.approx(
        SCRIBE.page_width / mm * 72, abs=0.6
    )
    assert float(page.mediabox.height) == pytest.approx(
        SCRIBE.page_height / mm * 72, abs=0.6
    )
