from pathlib import Path

import pytest
from pypdf import PdfReader

from parch import ConfigError
from parch.books import YearPlanner, book_for, outline_entries
from parch.components import DotGridPage
from parch.devices.registry import NAV_H, NOMAD, SCRIBE
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    CLONE_DOT,
    CLONE_DOT_PITCH,
    HAIR,
    HEADER_H,
    INK,
    RULE_C,
    SOFT,
    dot_grid_page_rect,
    paint_dot_grid,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.sections.dot_grid import DotGridSection
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


def test_dot_grid_off_by_default():
    spec = Spec(notes_pages=1)
    dests = [page.dest for page in YearPlanner().pages(spec)]
    assert spec.dot_grid_pages == 0
    assert "dot-grid-2026" not in dests
    assert dests[:3] == ["cover", "year-2026", "quarter-2026-Q1"]
    assert DotGridSection(spec).pages() == []
    assert dests[-1] != "dot-grid-2026"


def test_year_planner_inserts_dot_grid_after_tasks_when_enabled():
    spec = Spec(dot_grid_pages=2, months=(1,), notes_pages=0)
    pages = YearPlanner().pages(spec)
    dests = [page.dest for page in pages]
    extras = DotGridSection(spec).pages()
    assert [page.dest for page in extras] == ["dot-grid-2026", "dot-grid-2026-02"]
    assert dests[-2:] == ["dot-grid-2026", "dot-grid-2026-02"]
    last_task = max(i for i, page in enumerate(pages) if page.kind.startswith("task"))
    assert dests[last_task + 1 :] == ["dot-grid-2026", "dot-grid-2026-02"]
    assert (
        dests.index("cover") < dests.index("year-2026") < dests.index("quarter-2026-Q1")
    )
    first = next(page for page in pages if page.kind == "dot_grid")
    assert first.title == "Dot grid"
    assert first.dest == spec.dot_grid_dest
    assert first.nav == ()
    sheet = next(item for item in first.components if isinstance(item, DotGridPage))
    assert sheet.page == 1
    assert sheet.pages == 2
    assert extras[1].components[0].page == 2


def test_spec_dot_grid_dests_and_toml():
    spec = Spec(dot_grid_pages=2)
    assert spec.dot_grid_dest == "dot-grid-2026"
    assert spec.dest_for_dot_grid(1) == "dot-grid-2026"
    assert spec.dest_for_dot_grid(2) == "dot-grid-2026-02"
    assert Spec.from_mapping({"dot_grid": True}).dot_grid_pages == 1
    assert Spec.from_mapping({"dot_grid": False}).dot_grid_pages == 0
    assert Spec.from_mapping({"dot_grid_pages": 3}).dot_grid_pages == 3
    example = Spec.from_path(Path("examples/nomad-dot-grid.toml"))
    assert example.book == "year-planner"
    assert example.dot_grid_pages == 2
    assert example.notes_pages == 0
    assert example.months == (1,)
    with pytest.raises(ConfigError, match="dot_grid must be a boolean"):
        Spec.from_mapping({"dot_grid": 2})
    with pytest.raises(ConfigError, match="dot_grid_pages must be 0–100"):
        Spec(dot_grid_pages=101)
    with pytest.raises(ConfigError, match="dot_grid_pages must be >= 1"):
        Spec().dest_for_dot_grid(1)
    with pytest.raises(ConfigError, match="dot grid page out of range"):
        spec.dest_for_dot_grid(3)


def test_dot_grid_page_rect_is_full_bleed():
    for device in (NOMAD, SCRIBE):
        box = dot_grid_page_rect(device)
        assert box == Rect(0.0, 0.0, device.page_width, device.page_height)
        well = well_rect(device)
        assert box.x < well.x
        assert box.y < well.y
        assert box.right > well.right
        assert box.bottom > well.bottom
        frame = device.content_frame()
        assert box.bottom > frame.bottom
        assert box.w > frame.w


def test_paint_dot_grid_reuses_clone_pitch_and_bleeds_past_chrome():
    sheet = DotGridPage(page=1, pages=1)
    ink = RecordingPlotter()
    paint_dot_grid(ink, NOMAD, sheet)
    assert _texts(ink) == []
    dots = _dots(ink)
    box = dot_grid_page_rect(NOMAD)
    inset = Rect(box.x + 1.1, box.y + 1.2, box.w - 2.2, box.h - 2.4)
    nx = max(2, int(inset.w / CLONE_DOT_PITCH))
    ny = max(2, int(inset.h / CLONE_DOT_PITCH))
    assert len(dots) == nx * ny
    assert len(dots) > 30
    assert all(op[5] == pytest.approx(RULE_C) for op in dots)
    xs = [op[1].x for op in dots]
    ys = [op[1].y for op in dots]
    assert min(xs) < NOMAD.writing_clearance
    assert max(op[1].right for op in dots) > NOMAD.page_width - NOMAD.writing_clearance
    assert min(ys) < NOMAD.top_clearance
    strip_y = NOMAD.page_height - NOMAD.bottom_clearance - NAV_H
    assert max(op[1].bottom for op in dots) > strip_y
    well = well_rect(NOMAD)
    outside = [
        op
        for op in dots
        if op[1].y < well.y
        or op[1].bottom > well.bottom
        or op[1].x < well.x
        or op[1].right > well.right
    ]
    assert outside
    frames = [
        op for op in ink.ops if op[0] == "rect" and op[1] == box and op[2] and not op[3]
    ]
    assert frames
    assert frames[0][4] == pytest.approx(HAIR)
    assert frames[0][6] == pytest.approx(SOFT)


def test_layout_skips_header_and_nav_strip():
    spec = Spec(dot_grid_pages=1, months=(1,), notes_pages=0)
    page = DotGridSection(spec).pages()[0]
    assert strip_active(page.kind) == ""
    assert strip_items(page) == ()
    for device in (NOMAD, SCRIBE):
        ink = RecordingPlotter()
        PlannerLayout().paint(page, ink, device)
        texts = _texts(ink)
        assert texts == []
        assert "Year" not in texts
        assert "Quar" not in texts
        assert "Task" not in texts
        assert "Dot grid" not in texts
        assert "Notes" not in texts
        slabs = [
            op
            for op in ink.ops
            if op[0] == "rect"
            and op[3]
            and op[1].y == pytest.approx(device.content_top)
            and op[1].h == pytest.approx(HEADER_H)
            and op[5] == pytest.approx(INK)
        ]
        assert not slabs
        top_fills = [
            op
            for op in ink.ops
            if op[0] == "rect"
            and op[3]
            and op[1].y == pytest.approx(0.0)
            and op[1].w == pytest.approx(device.page_width)
            and op[1].h == pytest.approx(device.top_clearance + HEADER_H)
        ]
        assert not top_fills
        strip_y = device.page_height - device.bottom_clearance - NAV_H
        wash = [
            op
            for op in ink.ops
            if op[0] == "rect"
            and op[3]
            and op[1].y == pytest.approx(strip_y)
            and op[1].w == pytest.approx(device.page_width)
        ]
        assert not wash
        assert strip_active("dot_grid") == ""


def test_dot_grid_is_year_planner_extra_not_a_notebook():
    """DG4 stays on YearPlanner. A cover notebook is a later follow-up."""
    with pytest.raises(ConfigError, match="book must be"):
        Spec.from_mapping({"book": "dot-grid-notebook", "dot_grid_pages": 1})
    with pytest.raises(ConfigError, match="book must be"):
        book_for("dot-grid-notebook")
    spec = Spec(dot_grid_pages=1, months=(1,), notes_pages=0)
    assert spec.book == "year-planner"
    assert book_for(spec.book) is YearPlanner
    pages = YearPlanner().pages(spec)
    kinds = [page.kind for page in pages]
    assert kinds[0] == "cover"
    assert "annual" in kinds
    assert kinds[-1] == "dot_grid"
    assert kinds.count("dot_grid") == 1
    assert kinds.count("cover") == 1


def test_dot_grid_does_not_add_strip_chip_on_other_pages():
    spec = Spec(notes_pages=1, months=(1,), dot_grid_pages=2)
    year = next(page for page in YearPlanner().pages(spec) if page.kind == "annual")
    labels = [label for label, _dest in strip_items(year)]
    assert labels == [
        "Year",
        "Quar",
        "Mon",
        "Habit",
        "Week",
        "Rev",
        "Day",
        "Notes",
        "Proj",
        "Meet",
        "Task",
    ]
    assert "Dot" not in labels
    assert "Grid" not in labels


def test_year_planner_outline_omits_dot_grid():
    spec = Spec(months=(1,), notes_pages=0, outline=True, dot_grid_pages=2)
    pages = YearPlanner().pages(spec)
    dests = [dest for _title, dest in outline_entries(pages)]
    assert spec.dot_grid_dest not in dests
    assert spec.dest_for_dot_grid(2) not in dests
    assert any(page.kind == "dot_grid" for page in pages)


def test_press_example_toml_appends_bleed_pages(tmp_path: Path):
    out = tmp_path / "nomad-dot-grid.pdf"
    spec = Spec.from_path(Path("examples/nomad-dot-grid.toml"))
    press(spec, out)
    dests = [page.dest for page in YearPlanner().pages(spec)]
    reader = PdfReader(out)
    assert dests[-2:] == [spec.dot_grid_dest, spec.dest_for_dot_grid(2)]
    assert len(reader.pages) == len(dests)
    named = {str(key).lstrip("/") for key in (reader.named_destinations or {})}
    assert spec.year_dest in named
    assert spec.dot_grid_dest in named
    assert spec.dest_for_dot_grid(2) in named
