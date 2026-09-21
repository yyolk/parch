from pathlib import Path

import pytest
from pypdf import PdfReader

from parch import ConfigError
from parch.books import (
    DotGrid,
    EngineeringNotebook,
    ProjectsNotebook,
    YearPlanner,
    book_for,
)
from parch.components import DotGridSheet
from parch.devices.registry import NOMAD, SCRIBE
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.painters import (
    CLONE_DOT,
    CLONE_DOT_PITCH,
    HAIR,
    HEADER_H,
    RULE_C,
    SOFT,
    _paint_clone_dot_grid,
    dot_grid_page,
    paint_dot_grid,
)
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.sections.dot_grid import DotGridSection
from parch.spec import Spec


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
    spec = Spec(book="dot-grid", dot_grid_sheets=2)
    pages = DotGridSection(spec).pages()
    assert [page.kind for page in pages] == ["dot_grid", "dot_grid"]
    assert [page.dest for page in pages] == ["dot-grid-2026-01", "dot-grid-2026-02"]
    first = pages[0].components[0]
    assert isinstance(first, DotGridSheet)
    assert first.sheet == 1
    assert first.sheets == 2
    assert pages[0].nav == ()
    assert pages[0].title == "Dot grid"


def test_section_empty_when_no_sheets():
    assert DotGridSection(Spec()).pages() == []


def test_spec_dot_grid_dests_and_toml():
    spec = Spec(book="dot-grid", dot_grid_sheets=1)
    assert spec.dest_for_dot_grid(1) == "dot-grid-2026-01"
    example = Spec.from_path(Path("examples/dot-grid.toml"))
    assert example.book == "dot-grid"
    assert example.dot_grid_sheets == 8
    assert example.device == "supernote-nomad"
    assert example.year == 2026
    assert example.title == "Dot grid"
    assert Spec.from_mapping({"dot_grid": {"sheets": 2}}).dot_grid_sheets == 2
    assert Spec.from_mapping({"dot_grid_sheets": 3}).dot_grid_sheets == 3
    with pytest.raises(ConfigError, match="dot_grid_sheets must be 0–100"):
        Spec(dot_grid_sheets=101)
    with pytest.raises(ConfigError, match="dot_grid_sheets must be >= 1"):
        Spec().dest_for_dot_grid(1)
    with pytest.raises(ConfigError, match="dot-grid sheet out of range"):
        spec.dest_for_dot_grid(2)


def test_dot_grid_requires_sheets():
    with pytest.raises(ConfigError, match="dot-grid requires dot_grid_sheets >= 1"):
        Spec(book="dot-grid")


def test_dot_grid_rejects_pad_sheet_counts():
    with pytest.raises(ConfigError, match="dot-grid cannot set engineering_sheets"):
        Spec(book="dot-grid", dot_grid_sheets=1, engineering_sheets=1)
    with pytest.raises(ConfigError, match="dot-grid cannot set steno_sheets"):
        Spec(book="dot-grid", dot_grid_sheets=1, steno_sheets=1)


def test_book_is_coverless_n_sheets():
    spec = Spec(book="dot-grid", dot_grid_sheets=3, title="Dot grid")
    pages = DotGrid().pages(spec)
    assert [page.kind for page in pages] == ["dot_grid", "dot_grid", "dot_grid"]
    assert len(pages) == spec.dot_grid_sheets
    assert all(page.nav == () for page in pages)
    assert pages[0].dest == spec.dest_for_dot_grid(1)
    assert pages[2].dest == spec.dest_for_dot_grid(3)
    assert spec.cover_dest not in {page.dest for page in pages}
    assert spec.year_dest not in {page.dest for page in pages}
    assert isinstance(pages[0].components[0], DotGridSheet)


def test_book_for_selects_dot_grid():
    spec = Spec.from_path(Path("examples/dot-grid.toml"))
    assert book_for(spec.book) is DotGrid
    assert book_for("dot-grid") is DotGrid
    assert book_for("year-planner") is YearPlanner
    assert book_for("projects-notebook") is ProjectsNotebook
    assert book_for("engineering-notebook") is EngineeringNotebook


def test_paint_reuses_clone_dot_grid_on_full_page():
    box = dot_grid_page(NOMAD)
    assert box.x == 0.0
    assert box.y == 0.0
    assert box.w == pytest.approx(NOMAD.page_width)
    assert box.h == pytest.approx(NOMAD.page_height)
    clone = RecordingPlotter()
    _paint_clone_dot_grid(clone, box)
    painted = RecordingPlotter()
    paint_dot_grid(painted, NOMAD, DotGridSheet(sheet=1, sheets=1))
    assert painted.ops == clone.ops
    assert CLONE_DOT_PITCH == pytest.approx(2.8)
    assert CLONE_DOT == pytest.approx(0.32)


def test_paint_is_edge_to_edge_not_content_frame():
    ink = RecordingPlotter()
    paint_dot_grid(ink, NOMAD, DotGridSheet(sheet=1, sheets=1))
    page = dot_grid_page(NOMAD)
    frames = [
        op
        for op in ink.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1] == page
    ]
    assert frames
    assert all(op[4] == pytest.approx(HAIR) for op in frames)
    assert all(op[6] == pytest.approx(SOFT) for op in frames)
    dots = _dots(ink)
    assert len(dots) > 100
    assert all(op[5] == pytest.approx(RULE_C) for op in dots)
    frame = NOMAD.content_frame()
    assert any(op[1].y < frame.y for op in dots)
    assert any(op[1].x < frame.x for op in dots)
    assert any(op[1].right > frame.right for op in dots)
    assert any(op[1].bottom > frame.bottom for op in dots)


def test_layout_skips_header_and_nav():
    spec = Spec(book="dot-grid", dot_grid_sheets=1)
    page = DotGrid().pages(spec)[0]
    for device in (NOMAD, SCRIBE):
        ink = RecordingPlotter()
        PlannerLayout().paint(page, ink, device)
        texts = [op[2] for op in ink.ops if op[0] == "text"]
        assert texts == []
        header = [
            op
            for op in ink.ops
            if op[0] == "rect"
            and op[3]
            and op[1].y == pytest.approx(0.0)
            and op[1].h == pytest.approx(device.top_clearance + HEADER_H)
        ]
        assert header == []
        assert ink.links() == []
        assert _dots(ink)


def test_press_selects_dot_grid_from_toml(tmp_path: Path):
    spec = Spec.from_path(Path("examples/dot-grid.toml"))
    assert spec.book == "dot-grid"
    assert spec.dot_grid_sheets == 8
    assert book_for(spec.book) is DotGrid

    out = tmp_path / "dot-grid.pdf"
    press(spec, out)
    dests = {str(key).lstrip("/") for key in (PdfReader(out).named_destinations or {})}
    assert spec.cover_dest not in dests
    assert spec.year_dest not in dests
    assert spec.dest_for_dot_grid(1) in dests
    assert spec.dest_for_dot_grid(8) in dests
    assert spec.projects_index_dest not in dests
    assert len(PdfReader(out).pages) == spec.dot_grid_sheets
