"""Engineering pad duplex — paired front/back page kinds (E4)."""

from pathlib import Path

import pytest
from pypdf import PdfReader

from parch.books import EngineeringPad, ProjectsNotebook, YearPlanner, book_for
from parch.components import EngineeringPadBack, EngineeringPadFront
from parch.devices.registry import NOMAD
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.painters import (
    ENG_PAD_HEAD_COL_GAP,
    ENG_PAD_HEAD_WEIGHTS,
    ENG_PAD_LABEL_W,
    ENG_PAD_MAJOR,
    HAIR,
    MUTED,
    RULE,
    engineering_grid_counts,
    engineering_grid_lines,
    engineering_pad_header_height,
    engineering_pad_header_rows,
    engineering_pad_seats,
    engineering_pad_sheet_parts,
    paint_engineering_pad_back,
    paint_engineering_pad_front,
)
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.sections.engineering_pad import EngineeringPadSection
from parch.spec import Spec


def _texts(plotter: RecordingPlotter) -> list[str]:
    return [op[2] for op in plotter.ops if op[0] == "text"]


def _lines(plotter: RecordingPlotter) -> list[tuple]:
    return [op for op in plotter.ops if op[0] == "line"]


def _rects(plotter: RecordingPlotter) -> list[tuple]:
    return [op for op in plotter.ops if op[0] == "rect"]


def test_section_emits_front_back_pairs():
    spec = Spec(book="engineering-pad", engineering_pad_sheets=3)
    pages = EngineeringPadSection(spec).pages()
    assert len(pages) == 6
    assert [page.kind for page in pages] == [
        "engineering_pad_front",
        "engineering_pad_back",
        "engineering_pad_front",
        "engineering_pad_back",
        "engineering_pad_front",
        "engineering_pad_back",
    ]
    fronts = [p for p in pages if p.kind == "engineering_pad_front"]
    backs = [p for p in pages if p.kind == "engineering_pad_back"]
    assert [p.components[0] for p in fronts] == [
        EngineeringPadFront(year=2026, sheet=n, sheets=3) for n in (1, 2, 3)
    ]
    assert [p.components[0] for p in backs] == [
        EngineeringPadBack(year=2026, sheet=n, sheets=3) for n in (1, 2, 3)
    ]
    assert [p.dest for p in pages] == [
        "engineering-pad-2026-01-front",
        "engineering-pad-2026-01-back",
        "engineering-pad-2026-02-front",
        "engineering-pad-2026-02-back",
        "engineering-pad-2026-03-front",
        "engineering-pad-2026-03-back",
    ]
    assert all(page.nav == () for page in pages)
    assert all(page.title == "Engineering pad" for page in pages)


def test_paired_kinds_are_distinct_painters():
    assert paint_engineering_pad_front is not paint_engineering_pad_back
    assert paint_engineering_pad_front.__name__ == "paint_engineering_pad_front"
    assert paint_engineering_pad_back.__name__ == "paint_engineering_pad_back"


def test_year_planner_does_not_include_pad():
    pages = YearPlanner().pages(Spec(months=(1,), notes_pages=0))
    assert not any(
        page.kind in {"engineering_pad_front", "engineering_pad_back"} for page in pages
    )
    assert "engineering-pad-2026-01-front" not in {page.dest for page in pages}


def test_demo_book_is_section_only():
    spec = Spec(book="engineering-pad", engineering_pad_sheets=2)
    assert book_for(spec.book) is EngineeringPad
    assert book_for("year-planner") is YearPlanner
    assert book_for("projects-notebook") is ProjectsNotebook
    pages = EngineeringPad().pages(spec)
    assert pages == EngineeringPadSection(spec).pages()
    assert {page.kind for page in pages} == {
        "engineering_pad_front",
        "engineering_pad_back",
    }
    assert not any(page.kind == "cover" for page in pages)


def test_header_seats_three_labeled_rows():
    frame = NOMAD.content_frame()
    head, well = engineering_pad_seats(frame)
    assert head.y == pytest.approx(frame.y)
    assert head.h == pytest.approx(engineering_pad_header_height())
    assert well.y == pytest.approx(head.bottom)
    assert well.bottom == pytest.approx(frame.bottom)
    assert well.x == pytest.approx(frame.x)
    assert well.w == pytest.approx(frame.w)
    rows = engineering_pad_header_rows(head)
    assert len(rows) == 3
    (title, number), (name, dated), (subject, sheet) = rows
    assert title.w > number.w
    assert name.w > dated.w
    assert subject.w > sheet.w
    assert number.x == pytest.approx(title.right + ENG_PAD_HEAD_COL_GAP)
    assert ENG_PAD_HEAD_WEIGHTS[0] > ENG_PAD_HEAD_WEIGHTS[1]
    assert ENG_PAD_LABEL_W < title.w / 2
    tag, num, of, total = engineering_pad_sheet_parts(sheet)
    assert tag.x == pytest.approx(sheet.x)
    assert total.right == pytest.approx(sheet.right)
    assert num.x > tag.x
    assert of.x > num.x


def test_front_paints_header_blank_well_no_grid():
    front = EngineeringPadFront(year=2026, sheet=1, sheets=2)
    frame = NOMAD.content_frame()
    plotter = RecordingPlotter()
    paint_engineering_pad_front(plotter, frame, front)
    texts = _texts(plotter)
    assert texts.count("Title") == 1
    assert texts.count("No.") == 1
    assert texts.count("Name") == 1
    assert texts.count("Date") == 1
    assert texts.count("Subject") == 1
    assert texts.count("Sheet") == 1
    assert texts.count("of") == 1
    assert texts.count("1") == 1
    assert texts.count("2") == 1
    head, well = engineering_pad_seats(frame)
    well_lines = [
        op
        for op in _lines(plotter)
        if min(op[2], op[4]) > head.bottom + 0.05
        and max(op[2], op[4]) < well.bottom - 0.05
    ]
    assert well_lines == []
    outer = [
        op
        for op in _rects(plotter)
        if op[1].x == pytest.approx(frame.x)
        and op[1].y == pytest.approx(frame.y)
        and op[1].w == pytest.approx(frame.w)
        and op[1].h == pytest.approx(frame.h)
    ]
    assert len(outer) == 1
    assert outer[0][4] == pytest.approx(HAIR)
    assert outer[0][6] == pytest.approx(MUTED)


def test_back_paints_five_by_five_grid_no_header():
    back = EngineeringPadBack(year=2026, sheet=1, sheets=2)
    frame = NOMAD.content_frame()
    plotter = RecordingPlotter()
    paint_engineering_pad_back(plotter, frame, back)
    texts = _texts(plotter)
    assert "Title" not in texts
    assert "Name" not in texts
    assert "Subject" not in texts
    assert "Sheet" not in texts
    nx, ny = engineering_grid_counts(frame)
    assert nx % ENG_PAD_MAJOR == 0
    assert ny % ENG_PAD_MAJOR == 0
    assert nx >= ENG_PAD_MAJOR
    assert ny >= ENG_PAD_MAJOR
    expected = engineering_grid_lines(frame)
    assert len(expected) == (nx - 1) + (ny - 1)
    majors = [line for line in expected if line[4]]
    minors = [line for line in expected if not line[4]]
    assert majors
    assert minors
    pitch_x = frame.w / nx
    for i in range(1, nx):
        x = frame.x + i * pitch_x
        line = next(item for item in expected if item[0] == pytest.approx(x))
        assert line[4] is (i % ENG_PAD_MAJOR == 0)
    for x1, y1, x2, y2, major in expected:
        match = [
            op
            for op in _lines(plotter)
            if op[1] == pytest.approx(x1)
            and op[2] == pytest.approx(y1)
            and op[3] == pytest.approx(x2)
            and op[4] == pytest.approx(y2)
            and op[5] == pytest.approx(HAIR if major else RULE)
            and op[6] == pytest.approx(MUTED)
        ]
        assert match, f"missing grid line {(x1, y1, x2, y2, major)}"


def test_no_binder_holes_or_hole_margin():
    frame = NOMAD.content_frame()
    assert frame.x == pytest.approx(NOMAD.writing_clearance)
    assert frame.right == pytest.approx(NOMAD.page_width - NOMAD.writing_clearance)
    front = RecordingPlotter()
    paint_engineering_pad_front(
        front, frame, EngineeringPadFront(year=2026, sheet=1, sheets=1)
    )
    back = RecordingPlotter()
    paint_engineering_pad_back(
        back, frame, EngineeringPadBack(year=2026, sheet=1, sheets=1)
    )
    for plotter in (front, back):
        for op in _rects(plotter):
            box = op[1]
            assert box.x >= frame.x - 0.01
            assert box.right <= frame.right + 0.01
            # No hole-margin strip: nothing sits in the left writing-clearance gutter.
            assert box.x != pytest.approx(0.0) or box.w > NOMAD.page_width / 2
        for op in _lines(plotter):
            assert min(op[1], op[3]) >= frame.x - 0.01


def test_layout_skips_planner_chrome():
    spec = Spec(book="engineering-pad", engineering_pad_sheets=1)
    pages = EngineeringPadSection(spec).pages()
    front = next(p for p in pages if p.kind == "engineering_pad_front")
    back = next(p for p in pages if p.kind == "engineering_pad_back")
    layout = PlannerLayout()
    for page in (front, back):
        plotter = RecordingPlotter()
        layout.paint(page, plotter, NOMAD)
        texts = _texts(plotter)
        assert "Year" not in texts
        assert "Engineering pad" not in texts  # page.title is not the pad header
        fills = [op for op in _rects(plotter) if op[3] is True]
        assert fills == []  # no black header slab, no nav wash
        if page.kind == "engineering_pad_front":
            assert "Title" in texts
            assert "Sheet" in texts
        else:
            assert "Title" not in texts
            assert "Sheet" not in texts


def test_press_demo_toml_duplex_pages(tmp_path):
    spec = Spec.from_path(Path("examples/engineering-pad.toml"))
    assert spec.book == "engineering-pad"
    assert spec.engineering_pad_sheets == 2
    out = tmp_path / "pad.pdf"
    press(spec, out)
    reader = PdfReader(out)
    assert len(reader.pages) == 4
    dests = {str(key).lstrip("/") for key in (reader.named_destinations or {})}
    assert "engineering-pad-2026-01-front" in dests
    assert "engineering-pad-2026-01-back" in dests
    assert "engineering-pad-2026-02-front" in dests
    assert "engineering-pad-2026-02-back" in dests
    assert "cover" not in dests
    assert "year-2026" not in dests


def test_layout_plot_records_pair():
    spec = Spec(book="engineering-pad", engineering_pad_sheets=1)
    plotter = RecordingPlotter()
    EngineeringPad().plot(spec, plotter)
    assert plotter.dests() == [
        "engineering-pad-2026-01-front",
        "engineering-pad-2026-01-back",
    ]
    assert plotter.page == 2
