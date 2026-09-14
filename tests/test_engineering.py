from pathlib import Path

import pytest
from pypdf import PdfReader

from parch import ConfigError
from parch.components import EngineeringPad
from parch.devices.registry import NOMAD, SCRIBE
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.painters import (
    ENG_HEADER_FIELDS,
    ENG_HEADER_H,
    ENG_MAJOR_EVERY,
    HAIR,
    HEADER_H,
    INK,
    MUTED,
    RULE,
    RULE_C,
    EngineeringGridMesh,
    engineering_front_seats,
    engineering_grid_mesh,
    engineering_header_cells,
    paint_engineering_pad,
)
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.sections.engineering import EngineeringPadSection
from parch.spec import Spec


def _texts(plotter: RecordingPlotter) -> list[str]:
    return [op[2] for op in plotter.text_ops()]


def _lines(plotter: RecordingPlotter) -> list[tuple]:
    return [op for op in plotter.ops if op[0] == "line"]


def test_section_emits_duplex_pair_per_sheet():
    spec = Spec(engineering_sheets=2)
    pages = EngineeringPadSection(spec).pages()
    assert [page.kind for page in pages] == [
        "engineering_front",
        "engineering_back",
        "engineering_front",
        "engineering_back",
    ]
    assert [page.dest for page in pages] == [
        "engineering-2026-01-front",
        "engineering-2026-01-back",
        "engineering-2026-02-front",
        "engineering-2026-02-back",
    ]
    front = pages[0].components[0]
    back = pages[1].components[0]
    assert isinstance(front, EngineeringPad)
    assert front.face == "front"
    assert back.face == "back"
    assert front.sheet == back.sheet == 1
    assert front.sheets == 2
    assert pages[0].nav == ()


def test_section_empty_when_no_sheets():
    assert EngineeringPadSection(Spec()).pages() == []


def test_spec_engineering_dests_and_toml():
    spec = Spec(engineering_sheets=1)
    assert spec.dest_for_engineering_pad(1, "front") == "engineering-2026-01-front"
    assert spec.dest_for_engineering_pad(1, "back") == "engineering-2026-01-back"
    example = Spec.from_path(Path("examples/engineering-pad.toml"))
    assert example.engineering_sheets == 1
    assert example.device == "supernote-nomad"
    assert example.year == 2026
    assert "year =" not in Path("examples/engineering-pad.toml").read_text()
    assert Spec.from_mapping({"engineering": {"sheets": 2}}).engineering_sheets == 2
    with pytest.raises(ConfigError, match="engineering_sheets must be 0–24"):
        Spec(engineering_sheets=25)
    with pytest.raises(ConfigError, match="front or back"):
        spec.dest_for_engineering_pad(1, "verso")
    with pytest.raises(ConfigError, match="engineering_sheets must be >= 1"):
        Spec().dest_for_engineering_pad(1, "front")
    with pytest.raises(ConfigError, match="engineering sheet out of range"):
        spec.dest_for_engineering_pad(2, "front")


def test_grid_mesh_is_square_with_majors_every_five():
    for device in (NOMAD, SCRIBE):
        mesh = engineering_grid_mesh(device.content_frame())
        assert isinstance(mesh, EngineeringGridMesh)
        assert mesh.nx % ENG_MAJOR_EVERY == 0
        assert mesh.ny % ENG_MAJOR_EVERY == 0
        assert mesh.nx >= ENG_MAJOR_EVERY
        assert mesh.pitch == pytest.approx(mesh.origin.w / mesh.nx)
        assert mesh.pitch == pytest.approx(mesh.origin.h / mesh.ny)
        left = mesh.origin.x - device.content_frame().x
        right = device.content_frame().right - mesh.origin.right
        assert left == pytest.approx(right, abs=1e-6)


def test_front_seats_use_symmetric_content_frame():
    frame = NOMAD.content_frame()
    header, well = engineering_front_seats(frame)
    assert header.h == pytest.approx(ENG_HEADER_H)
    assert frame.x == pytest.approx(NOMAD.writing_clearance)
    assert NOMAD.page_width - frame.right == pytest.approx(NOMAD.writing_clearance)
    assert header.y == pytest.approx(frame.y)
    assert well.y == pytest.approx(header.bottom)
    assert well.bottom == pytest.approx(frame.bottom)
    assert well.x == pytest.approx(frame.x)
    cells = engineering_header_cells(header)
    assert len(cells) == 3
    subject, dated, sheet = cells
    assert subject.w == pytest.approx(header.w * 0.50)
    assert dated.w == pytest.approx(sheet.w)
    assert dated.w == pytest.approx(header.w * 0.25)
    assert subject.w > dated.w


def test_front_paints_three_boxed_cells_without_grid():
    pad = EngineeringPad(face="front", sheet=1, sheets=1)
    ink = RecordingPlotter()
    paint_engineering_pad(ink, NOMAD, pad)
    texts = _texts(ink)
    assert texts == list(ENG_HEADER_FIELDS)
    assert "Notes" not in texts
    assert "Title" not in texts
    assert "No." not in texts
    assert "Name" not in texts
    assert "of" not in texts
    assert "1" not in texts
    lines = _lines(ink)
    back = RecordingPlotter()
    paint_engineering_pad(back, NOMAD, EngineeringPad(face="back", sheet=1, sheets=1))
    assert len(lines) < len(_lines(back)) / 2
    frames = [
        op
        for op in ink.ops
        if op[0] == "rect" and op[1] == NOMAD.content_frame() and op[2] and not op[3]
    ]
    assert frames
    assert frames[0][6] == pytest.approx(INK)


def test_back_paints_grid_without_header():
    pad = EngineeringPad(face="back", sheet=1, sheets=1)
    ink = RecordingPlotter()
    paint_engineering_pad(ink, NOMAD, pad)
    texts = _texts(ink)
    assert texts == []
    assert "Subject" not in texts
    assert "Sheet" not in texts
    mesh = engineering_grid_mesh(NOMAD.content_frame())
    vertical = [op for op in _lines(ink) if op[1] == op[3] and op[2] != op[4]]
    majors = [
        op
        for op in vertical
        if op[5] == pytest.approx(HAIR) and op[6] == pytest.approx(MUTED)
    ]
    minors = [
        op
        for op in vertical
        if op[5] == pytest.approx(RULE) and op[6] == pytest.approx(RULE_C)
    ]
    assert len(majors) == mesh.nx // ENG_MAJOR_EVERY + 1
    assert len(minors) == mesh.nx + 1 - len(majors)
    frames = [
        op
        for op in ink.ops
        if op[0] == "rect" and op[1] == NOMAD.content_frame() and op[2] and not op[3]
    ]
    assert frames
    assert frames[0][6] == pytest.approx(MUTED)


def test_layout_skips_planner_slab_and_nav():
    spec = Spec(engineering_sheets=1)
    page = EngineeringPadSection(spec).pages()[0]
    ink = RecordingPlotter()
    PlannerLayout().paint(page, ink, NOMAD)
    texts = _texts(ink)
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


def test_press_example_toml_is_two_duplex_pages(tmp_path: Path):
    out = tmp_path / "engineering-pad.pdf"
    spec = Spec.from_path(Path("examples/engineering-pad.toml"))
    press(spec, out)
    reader = PdfReader(out)
    assert len(reader.pages) == 2
    dests = {str(key).lstrip("/") for key in (reader.named_destinations or {})}
    assert spec.dest_for_engineering_pad(1, "front") in dests
    assert spec.dest_for_engineering_pad(1, "back") in dests
    assert spec.year_dest not in dests
