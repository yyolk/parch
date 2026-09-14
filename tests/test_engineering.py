"""Engineering computation pad — duplex seats (E2). Independent of a notebook book."""

from pathlib import Path

import pytest
from pypdf import PdfReader

from parch.books import YearPlanner, book_for
from parch.books.engineering_pad import EngineeringPad as EngineeringPadBook
from parch.components.engineering import EngineeringPad
from parch.devices import NOMAD, SCRIBE
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.engineering import (
    ENG_MAJOR,
    engineering_grid_counts,
    engineering_grid_seats,
    engineering_pad_seats,
    paint_engineering_back,
    paint_engineering_front,
    paint_engineering_pad,
)
from parch.layouts.planner.painters import HAIR, HEADER_H, MUTED, RULE, RULE_C
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.sections.engineering import EngineeringPadSection
from parch.spec import Spec


def _pad(face: str) -> EngineeringPad:
    return EngineeringPad(face=face, year=2026)


def _lines(ops: list) -> list[tuple]:
    return [op for op in ops if op[0] == "line"]


def _texts(ops: list) -> list[str]:
    return [op[2] for op in ops if op[0] == "text"]


def _line_in_box(op: tuple, box: Rect, *, pad: float = 0.2) -> bool:
    _, x1, y1, x2, y2, *_ = op
    return (
        box.x - pad <= min(x1, x2) <= box.right + pad
        and box.x - pad <= max(x1, x2) <= box.right + pad
        and box.y - pad <= min(y1, y2) <= box.bottom + pad
        and box.y - pad <= max(y1, y2) <= box.bottom + pad
    )


def test_engineering_pad_seats_header_then_well():
    frame = NOMAD.content_frame()
    seats = engineering_pad_seats(frame)
    assert seats.frame == frame
    assert seats.title.y == pytest.approx(frame.y)
    assert seats.number.y == pytest.approx(seats.title.y)
    assert seats.number.x > seats.title.right
    assert seats.name.y >= seats.title.bottom - 1e-9
    assert seats.date.y == pytest.approx(seats.name.y)
    assert seats.subject.y >= seats.name.bottom - 1e-9
    assert seats.sheet.x > seats.subject.right
    assert seats.well.y >= seats.subject.bottom - 1e-9
    assert seats.well.bottom == pytest.approx(frame.bottom)
    assert seats.well.x == pytest.approx(frame.x)
    assert seats.well.w == pytest.approx(frame.w)
    assert seats.well.h > seats.title.h
    assert seats.title.x == pytest.approx(frame.x)
    assert seats.sheet.right == pytest.approx(frame.right)


def test_engineering_grid_seats_are_square_and_clustered():
    frame = NOMAD.content_frame()
    n_cols, n_rows = engineering_grid_counts(frame)
    assert n_cols % ENG_MAJOR == 0
    assert n_rows % ENG_MAJOR == 0
    assert n_cols >= ENG_MAJOR
    assert n_rows >= ENG_MAJOR
    seats = engineering_grid_seats(frame)
    assert len(seats.columns) == n_cols
    assert len(seats.rows) == n_rows
    pitch = seats.columns[0].w
    assert seats.rows[0].h == pytest.approx(pitch)
    assert seats.columns[-1].right == pytest.approx(seats.box.right)
    assert seats.rows[-1].bottom == pytest.approx(seats.box.bottom)
    assert seats.box.x >= frame.x - 1e-9
    assert seats.box.right <= frame.right + 1e-9
    assert seats.box.y >= frame.y - 1e-9
    assert seats.box.bottom <= frame.bottom + 1e-9


def test_engineering_grid_seats_scribe_is_square():
    frame = SCRIBE.content_frame()
    seats = engineering_grid_seats(frame)
    assert seats.columns[0].w == pytest.approx(seats.rows[0].h)
    assert len(seats.columns) % ENG_MAJOR == 0
    assert len(seats.rows) % ENG_MAJOR == 0


def test_front_paint_has_header_fields_and_blank_well():
    frame = NOMAD.content_frame()
    seats = engineering_pad_seats(frame)
    ink = RecordingPlotter()
    paint_engineering_front(ink, frame, _pad("front"))
    labels = _texts(ink.ops)
    for name in ("Title", "No.", "Name", "Date", "Subject", "Sheet", "of"):
        assert name in labels
    well_lines = [
        op
        for op in _lines(ink.ops)
        if _line_in_box(op, seats.well.inset(0.4, 0.4), pad=0)
    ]
    assert well_lines == []
    outers = [
        op
        for op in ink.ops
        if op[0] == "rect" and op[1] == frame and op[2] and not op[3]
    ]
    assert outers
    assert {op[6] for op in outers} == {MUTED}


def test_back_paint_is_grid_without_header():
    frame = NOMAD.content_frame()
    grid = engineering_grid_seats(frame)
    ink = RecordingPlotter()
    paint_engineering_back(ink, frame, _pad("back"))
    labels = _texts(ink.ops)
    assert labels == []
    lines = _lines(ink.ops)
    verts = [op for op in lines if op[1] == op[3]]
    horiz = [op for op in lines if op[2] == op[4]]
    assert len(verts) == len(grid.columns) + 1
    assert len(horiz) == len(grid.rows) + 1
    xs = sorted({op[1] for op in verts})
    majors = [op for op in verts if op[5] == HAIR]
    minors = [op for op in verts if op[5] == RULE]
    assert majors
    assert minors
    assert {op[6] for op in majors} == {MUTED}
    assert {op[6] for op in minors} == {RULE_C}
    for i, x in enumerate(xs):
        width = next(op[5] for op in verts if op[1] == x)
        if i % ENG_MAJOR == 0:
            assert width == HAIR
        else:
            assert width == RULE


def test_front_and_back_painters_do_not_share_marks():
    frame = NOMAD.content_frame()
    front = RecordingPlotter()
    back = RecordingPlotter()
    paint_engineering_pad(front, frame, _pad("front"))
    paint_engineering_pad(back, frame, _pad("back"))
    assert "Title" in _texts(front.ops)
    assert "Title" not in _texts(back.ops)
    assert len(_lines(back.ops)) > len(_lines(front.ops))


def test_section_emits_duplex_pair():
    spec = Spec(book="engineering-pad")
    pages = EngineeringPadSection(spec).pages()
    assert [page.kind for page in pages] == ["engineering_front", "engineering_back"]
    assert [page.dest for page in pages] == [
        spec.engineering_front_dest,
        spec.engineering_back_dest,
    ]
    assert all(page.nav == () for page in pages)
    faces = [page.components[0] for page in pages]
    assert all(isinstance(item, EngineeringPad) for item in faces)
    assert [item.face for item in faces] == ["front", "back"]


def test_demo_book_is_two_pages_not_a_notebook():
    spec = Spec(book="engineering-pad")
    book = EngineeringPadBook()
    pages = book.pages(spec)
    assert len(pages) == 2
    assert {page.kind for page in pages} == {"engineering_front", "engineering_back"}
    assert book_for("engineering-pad") is EngineeringPadBook
    assert book_for(spec.book) is EngineeringPadBook
    plotter = RecordingPlotter()
    book.plot(spec, plotter)
    assert plotter.dests() == [
        spec.engineering_front_dest,
        spec.engineering_back_dest,
    ]
    assert plotter.page == 2


def test_year_planner_does_not_grow_the_pad():
    spec = Spec(notes_pages=1)
    dests = {page.dest for page in YearPlanner().pages(spec)}
    assert spec.engineering_front_dest not in dests
    assert spec.engineering_back_dest not in dests
    assert not any(
        page.kind in {"engineering_front", "engineering_back"}
        for page in YearPlanner().pages(spec)
    )


def test_layout_uses_content_frame_and_skips_planner_chrome():
    spec = Spec(book="engineering-pad")
    pages = EngineeringPadSection(spec).pages()
    plotter = RecordingPlotter()
    for page in pages:
        plotter.begin_page()
        PlannerLayout().paint(page, plotter, NOMAD)
    frame = NOMAD.content_frame()
    assert frame.x == pytest.approx(NOMAD.writing_clearance)
    assert frame.x == pytest.approx(4.0)
    header_fills = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[3]
        and op[1].y == pytest.approx(NOMAD.content_top)
        and op[1].h == pytest.approx(HEADER_H)
    ]
    assert header_fills == []
    nav_washes = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[3] and op[1].y > NOMAD.page_height - 12
    ]
    assert nav_washes == []
    for op in plotter.ops:
        if op[0] in {"text", "rect"}:
            assert op[1].x >= frame.x - 0.01
            assert op[1].right <= frame.right + 0.01
            assert op[1].y >= frame.y - 0.01


def test_press_example_toml_is_two_named_pages(tmp_path: Path):
    spec = Spec.from_path(Path("examples/engineering-pad.toml"))
    assert spec.book == "engineering-pad"
    assert spec.device == "supernote-nomad"
    out = tmp_path / "engineering-pad.pdf"
    press(spec, out)
    reader = PdfReader(out)
    assert len(reader.pages) == 2
    dests = {str(key).lstrip("/") for key in (reader.named_destinations or {})}
    assert spec.engineering_front_dest in dests
    assert spec.engineering_back_dest in dests
    assert spec.year_dest not in dests
    assert spec.cover_dest not in dests


def test_press_scribe_duplex_geometry(tmp_path: Path):
    spec = Spec(book="engineering-pad", device="kindle-scribe")
    out = tmp_path / "scribe-pad.pdf"
    press(spec, out)
    page = PdfReader(out).pages[0]
    mm = 25.4
    assert float(page.mediabox.width) == pytest.approx(157.48 / mm * 72.0, abs=0.6)
    assert float(page.mediabox.height) == pytest.approx(209.97 / mm * 72.0, abs=0.6)
