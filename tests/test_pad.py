from pathlib import Path

import pytest
from pypdf import PdfReader

from parch import ConfigError
from parch.books import YearPlanner, book_for
from parch.components import PadBlank, PadGrid
from parch.devices import get_device
from parch.devices.registry import NOMAD
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    HEADER_H,
    MUTED,
    RULE_C,
    pad_grid_counts,
    paint_pad_grid,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.sections import EngineeringPadSection, PadSheet, sheet
from parch.sections.pad import sheet_label
from parch.spec import Spec


def test_sheet_builder_returns_paired_faces():
    spec = Spec(pad_sheets=4, notes_pages=1)
    unit = sheet(spec, 2, 4)
    assert isinstance(unit, PadSheet)
    assert unit.number == 2
    assert unit.of == 4
    assert unit.pages() == (unit.front, unit.back)
    assert unit.front.title == unit.back.title == "Sheet 2 of 4"
    assert unit.front.title == sheet_label(2, 4)
    assert unit.front.kind == "pad_front"
    assert unit.back.kind == "pad_back"
    assert unit.front.dest == spec.dest_for_pad(2)
    assert unit.back.dest == spec.dest_for_pad(2, back=True)
    front_well = unit.front.components[0]
    back_well = unit.back.components[0]
    assert isinstance(front_well, PadBlank)
    assert isinstance(back_well, PadGrid)
    assert (
        (front_well.number, front_well.of) == (back_well.number, back_well.of) == (2, 4)
    )
    assert front_well.year == back_well.year == spec.year
    assert back_well.major == 5


def test_section_flattens_sheet_tuples():
    spec = Spec(pad_sheets=3, notes_pages=1)
    section = EngineeringPadSection(spec)
    units = section.sheets()
    assert len(units) == 3
    assert [unit.number for unit in units] == [1, 2, 3]
    assert all(unit.of == 3 for unit in units)
    pages = section.pages()
    assert pages == [page for unit in units for page in unit.pages()]
    assert [page.kind for page in pages] == [
        "pad_front",
        "pad_back",
        "pad_front",
        "pad_back",
        "pad_front",
        "pad_back",
    ]
    assert [page.title for page in pages] == [
        "Sheet 1 of 3",
        "Sheet 1 of 3",
        "Sheet 2 of 3",
        "Sheet 2 of 3",
        "Sheet 3 of 3",
        "Sheet 3 of 3",
    ]


def test_zero_sheets_is_empty():
    spec = Spec(pad_sheets=0)
    assert EngineeringPadSection(spec).sheets() == []
    assert EngineeringPadSection(spec).pages() == []
    kinds = {page.kind for page in YearPlanner().pages(spec)}
    assert "pad_front" not in kinds
    assert "pad_back" not in kinds


def test_year_planner_inserts_flattened_sheets_after_review():
    spec = Spec(pad_sheets=2, notes_pages=1, months=(1,))
    pages = YearPlanner().pages(spec)
    dests = [page.dest for page in pages]
    review = dests.index(spec.review_index_dest)
    front = dests.index(spec.dest_for_pad(1))
    back = dests.index(spec.dest_for_pad(1, back=True))
    quarter = dests.index(spec.dest_for_quarter(1))
    assert review < front < back < dests.index(spec.dest_for_pad(2)) < quarter
    assert book_for(spec.book) is YearPlanner


def test_sheet_identity_in_header_not_on_back():
    spec = Spec(pad_sheets=2, notes_pages=1, months=(1,))
    pages = YearPlanner().pages(spec)
    front = next(page for page in pages if page.dest == spec.dest_for_pad(1))
    back = next(page for page in pages if page.dest == spec.dest_for_pad(1, back=True))
    assert front.title == back.title == "Sheet 1 of 2"
    assert strip_active(front.kind) == strip_active(back.kind) == "Pad"
    labels = [label for label, _ in strip_items(front)]
    assert "Pad" in labels
    assert labels.index("Notes") < labels.index("Pad") < labels.index("Proj")
    assert dict(strip_items(front))["Pad"] == spec.dest_for_pad(1)
    assert dict(strip_items(back))["Pad"] == spec.dest_for_pad(1)

    plotter = RecordingPlotter()
    YearPlanner().plot(spec, plotter)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Sheet 1 of 2" in texts
    assert "Sheet 2 of 2" in texts
    assert texts.count("Sheet 1 of 2") == 1
    assert texts.count("Sheet 2 of 2") == 1


def test_front_well_is_blank_back_is_five_by_five():
    spec = Spec(pad_sheets=1, notes_pages=0, months=(1,))
    pages = YearPlanner().pages(spec)
    front = next(page for page in pages if page.kind == "pad_front")
    back = next(page for page in pages if page.kind == "pad_back")
    assert isinstance(front.components[0], PadBlank)
    assert isinstance(back.components[0], PadGrid)

    header_well = well_rect(NOMAD)
    back_well = well_rect(NOMAD, header=False)
    assert back_well.y == pytest.approx(NOMAD.content_top + 2.2)
    assert header_well.y == pytest.approx(NOMAD.content_top + HEADER_H + 2.2)
    assert back_well.x == header_well.x == NOMAD.writing_clearance
    assert (
        back_well.w == header_well.w == NOMAD.page_width - 2 * NOMAD.writing_clearance
    )

    front_ink = RecordingPlotter()
    front_ink.begin_page()
    PlannerLayout().paint(front, front_ink, get_device(spec.device))
    front_lines = [op for op in front_ink.ops if op[0] == "line"]
    well_lines = [
        op
        for op in front_lines
        if header_well.y <= op[2] <= header_well.bottom
        or header_well.y <= op[4] <= header_well.bottom
    ]
    assert not well_lines

    grid_ink = RecordingPlotter()
    paint_pad_grid(grid_ink, back_well, back.components[0])
    lines = [op for op in grid_ink.ops if op[0] == "line"]
    pitch, cols, rows = pad_grid_counts(back_well, 5)
    assert cols % 5 == 0 and rows % 5 == 0
    assert len(lines) == (cols + 1) + (rows + 1)
    majors = [op for op in lines if op[6] == MUTED]
    minors = [op for op in lines if op[6] == RULE_C]
    assert len(majors) == (cols // 5 + 1) + (rows // 5 + 1)
    assert len(minors) == len(lines) - len(majors)
    assert pitch == pytest.approx(back_well.w / cols)
    circles = [op for op in grid_ink.ops if op[0] not in {"line", "rect", "text"}]
    assert not circles


def test_back_skips_header_slab():
    spec = Spec(pad_sheets=1, notes_pages=0, months=(1,))
    plotter = RecordingPlotter()
    YearPlanner().plot(spec, plotter)
    back_page = next(
        i
        for i, op in enumerate(plotter.ops)
        if op[0] == "add_dest" and op[1] == spec.dest_for_pad(1, back=True)
    )
    next_begin = next(
        (
            i
            for i, op in enumerate(plotter.ops[back_page + 1 :], start=back_page + 1)
            if op[0] == "begin_page"
        ),
        len(plotter.ops),
    )
    back_ops = plotter.ops[back_page:next_begin]
    header_slabs = [
        op
        for op in back_ops
        if op[0] == "rect" and op[3] and op[1].h == HEADER_H and op[5] == 0.0
    ]
    assert not header_slabs
    assert not any(op[0] == "text" and op[2].startswith("Sheet ") for op in back_ops)


def test_sheet_rejects_bad_index():
    spec = Spec(pad_sheets=2)
    with pytest.raises(ValueError, match="not in 1..2"):
        sheet(spec, 3, 2)
    with pytest.raises(ValueError, match="of must be"):
        sheet(spec, 1, 0)


def test_spec_pad_dests_and_toml():
    spec = Spec(pad_sheets=4)
    assert spec.pad_dest == "pad-2026-01"
    assert spec.dest_for_pad(1) == "pad-2026-01"
    assert spec.dest_for_pad(4, back=True) == "pad-2026-04-back"
    with pytest.raises(ConfigError, match="out of range"):
        spec.dest_for_pad(5)
    assert Spec.from_mapping({"pad": {"sheets": 8}}).pad_sheets == 8
    assert Spec.from_mapping({"pad_sheets": 2}).pad_sheets == 2
    assert Spec().pad_sheets == 0
    with pytest.raises(ConfigError, match="pad dest requires"):
        Spec().pad_dest
    with pytest.raises(ConfigError, match="0–48"):
        Spec(pad_sheets=49)
    loaded = Spec.from_path(Path("examples/pad.toml"))
    assert loaded.pad_sheets == 4
    assert loaded.months == (1,)
    assert loaded.book == "year-planner"


def test_press_pad_example_names_both_faces(tmp_path: Path):
    spec = Spec.from_path(Path("examples/pad.toml"))
    out = tmp_path / "pad.pdf"
    press(spec, out)
    dests = {str(key).lstrip("/") for key in (PdfReader(out).named_destinations or {})}
    assert spec.dest_for_pad(1) in dests
    assert spec.dest_for_pad(1, back=True) in dests
    assert spec.dest_for_pad(4) in dests
    assert spec.dest_for_pad(4, back=True) in dests
    assert spec.year_dest in dests
    pad_pages = [
        page for page in YearPlanner().pages(spec) if page.kind.startswith("pad_")
    ]
    assert len(pad_pages) == 8
