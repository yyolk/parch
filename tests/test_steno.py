from pathlib import Path

import pytest
from pypdf import PdfReader

from parch import ConfigError
from parch.components import StenoPad
from parch.devices.registry import NOMAD, SCRIBE
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import GREGG_PITCH_MM, steno_row_count, steno_seats
from parch.layouts.planner.painters import HAIR, HEADER_H, INK, MUTED, RULE, paint_steno
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.sections.steno import StenoSection
from parch.spec import Spec
from parch.tracks import columns, rows

MM_PER_INCH = 25.4
SIX_BY_NINE = (6 * MM_PER_INCH, 9 * MM_PER_INCH)


def _pt(mm: float) -> float:
    return mm / MM_PER_INCH * 72.0


def _texts(plotter: RecordingPlotter) -> list[str]:
    return [op[2] for op in plotter.text_ops()]


def _lines(plotter: RecordingPlotter) -> list[tuple]:
    return [op for op in plotter.ops if op[0] == "line"]


def test_section_emits_single_sided_pages():
    spec = Spec(steno_pages=2)
    pages = StenoSection(spec).pages()
    assert [page.kind for page in pages] == ["steno", "steno"]
    assert [page.dest for page in pages] == ["steno-2026-01", "steno-2026-02"]
    pad = pages[0].components[0]
    assert isinstance(pad, StenoPad)
    assert pad.sheet == 1
    assert pad.sheets == 2
    assert pages[0].nav == ()
    assert pages[0].title == spec.title


def test_section_empty_when_no_pages():
    assert StenoSection(Spec()).pages() == []


def test_spec_steno_dests_and_toml():
    spec = Spec(steno_pages=1)
    assert spec.dest_for_steno(1) == "steno-2026-01"
    example = Spec.from_path(Path("examples/steno.toml"))
    assert example.steno_pages == 1
    assert example.device == "supernote-nomad"
    assert example.engineering_sheets == 0
    assert Spec.from_mapping({"steno": {"pages": 2}}).steno_pages == 2
    with pytest.raises(ConfigError, match="steno_pages must be 0–24"):
        Spec(steno_pages=25)
    with pytest.raises(ConfigError, match="cannot both be set"):
        Spec(steno_pages=1, engineering_sheets=1)
    with pytest.raises(ConfigError, match="steno_pages must be >= 1"):
        Spec().dest_for_steno(1)
    with pytest.raises(ConfigError, match="steno sheet out of range"):
        spec.dest_for_steno(2)


def test_seats_are_rows_and_equal_columns():
    for device in (NOMAD, SCRIBE):
        frame = device.content_frame()
        bands, center = steno_seats(frame)
        n = steno_row_count(frame)
        assert n == round(frame.h / GREGG_PITCH_MM)
        assert bands == rows(frame, n)
        left, right = columns(frame, 2)
        assert center.x == pytest.approx(left.right)
        assert center.x == pytest.approx(frame.x + frame.w / 2)
        assert left.w == pytest.approx(right.w)
        assert bands[0].x == pytest.approx(frame.x)
        assert bands[0].w == pytest.approx(frame.w)
        assert bands[0].h == pytest.approx(GREGG_PITCH_MM, abs=0.2)
        assert device.page_width - frame.right == pytest.approx(
            device.writing_clearance
        )
        assert frame.x == pytest.approx(device.writing_clearance)


def test_paint_steno_only_inks_given_seats():
    bands = (Rect(1, 2, 10, 4), Rect(1, 6, 10, 4))
    center = Rect(6, 2, 0, 8)
    ink = RecordingPlotter()
    paint_steno(ink, bands, center)
    lines = _lines(ink)
    assert len(lines) == 3
    assert [op[0] for op in ink.ops] == ["line", "line", "line"]
    assert (lines[0][1], lines[0][2], lines[0][3], lines[0][4]) == (1, 6, 11, 6)
    assert (lines[1][1], lines[1][2], lines[1][3], lines[1][4]) == (1, 10, 11, 10)
    assert (lines[2][1], lines[2][2], lines[2][3], lines[2][4]) == (6, 2, 6, 10)
    assert lines[0][5] == pytest.approx(RULE)
    assert lines[0][6] == pytest.approx(MUTED)
    assert lines[2][5] == pytest.approx(HAIR)
    assert lines[2][6] == pytest.approx(INK)
    assert lines[2][5] > lines[0][5]
    assert _texts(ink) == []


def test_layout_skips_planner_slab_and_nav():
    spec = Spec(steno_pages=1)
    page = StenoSection(spec).pages()[0]
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
    frame = NOMAD.content_frame()
    bands, center = steno_seats(frame)
    lines = _lines(ink)
    horizontals = [op for op in lines if op[2] == op[4]]
    verticals = [op for op in lines if op[1] == op[3]]
    assert len(horizontals) == len(bands)
    assert len(verticals) == 1
    assert verticals[0][1] == pytest.approx(center.x)
    assert verticals[0][5] == pytest.approx(HAIR)
    for op, band in zip(horizontals, bands, strict=True):
        assert op[2] == pytest.approx(band.bottom)
        assert op[1] == pytest.approx(band.x)
        assert op[3] == pytest.approx(band.right)
        assert op[5] == pytest.approx(RULE)
        assert op[6] == pytest.approx(MUTED)
        assert frame.y <= op[2] <= frame.bottom + 1e-9


def test_year_planner_does_not_include_steno():
    from parch.books import YearPlanner

    kinds = {
        page.kind for page in YearPlanner().pages(Spec(notes_pages=1, months=(1,)))
    }
    assert "steno" not in kinds


def test_press_example_toml_is_one_nomad_page(tmp_path: Path):
    out = tmp_path / "steno.pdf"
    spec = Spec.from_path(Path("examples/steno.toml"))
    press(spec, out)
    reader = PdfReader(out)
    assert len(reader.pages) == 1
    page = reader.pages[0]
    assert float(page.mediabox.width) == pytest.approx(_pt(NOMAD.page_width), abs=0.6)
    assert float(page.mediabox.height) == pytest.approx(_pt(NOMAD.page_height), abs=0.6)
    assert float(page.mediabox.width) != pytest.approx(_pt(SIX_BY_NINE[0]), abs=0.6)
    assert float(page.mediabox.height) != pytest.approx(_pt(SIX_BY_NINE[1]), abs=0.6)
    dests = {str(key).lstrip("/") for key in (reader.named_destinations or {})}
    assert spec.dest_for_steno(1) in dests
    assert spec.year_dest not in dests
    assert "engineering-2026-01-front" not in dests
