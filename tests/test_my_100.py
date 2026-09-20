import shutil
from pathlib import Path

import pytest

from parch.books import YearPlanner
from parch.books.protocol import plot_pages
from parch.components import My100Page
from parch.devices.registry import NOMAD, SCRIBE
from parch.fonts.ramp import EffectiveRamp
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    MY_100_CHECK,
    MY_100_COUNT,
    MY_100_MAX_COLS,
    MY_100_MIN_COL_W,
    MY_100_MIN_ROW_H,
    MY_100_NUM_W,
    my_100_capacity,
    my_100_columns,
    my_100_grid,
    my_100_open_seat,
    my_100_page_count,
    my_100_page_numbers,
    my_100_row_h,
    my_100_row_parts,
    paint_my_100,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.plotter.fpdf2 import Fpdf2Plotter
from parch.sections.my_100 import My100Section
from parch.spec import Spec
from parch.specimen import render_page_png

_YEAR_STRIP = (
    ("Year", "year-2026"),
    ("Quar", "quarter-2026-Q1"),
    ("Mon", "month-2026-01"),
    ("Habit", "month-2026-01-habits"),
    ("Week", "week-2026-W01"),
    ("Rev", "review-index-2026"),
    ("Day", "2026-01-01"),
    ("Notes", "2026-01-01-notes-1"),
    ("Proj", "projects-index-2026-01"),
    ("Meet", "meetings-index-2026"),
    ("Task", "tasks-index-2026-Q1"),
)


def _on(**kwargs: object) -> Spec:
    kwargs.setdefault("notes_pages", 1)
    return Spec(my_100=True, **kwargs)


def _numbers(pages: list) -> list[int]:
    return [
        n
        for page in pages
        for item in page.components
        if isinstance(item, My100Page)
        for n in item.numbers
    ]


def test_my_100_off_by_default_and_section_empty():
    spec = Spec(notes_pages=1)
    assert spec.my_100 is False
    assert My100Section(spec).pages() == []
    dests = [page.dest for page in YearPlanner().pages(spec)]
    assert dests[1] == "year-2026"
    assert dests[2] == "quarter-2026-Q1"
    assert not any(dest.startswith("my-100-") for dest in dests)
    assert not any(page.kind == "my_100" for page in YearPlanner().pages(spec))


def test_my_100_inserts_after_annual_before_quarters():
    spec = _on()
    pages = YearPlanner().pages(spec)
    dests = [page.dest for page in pages]
    kinds = [page.kind for page in pages]
    annual = dests.index("year-2026")
    quarter = dests.index("quarter-2026-Q1")
    landing = dests.index("my-100-2026")
    assert dests[:2] == ["cover", "year-2026"]
    assert annual < landing < quarter
    assert dests[annual + 1] == "my-100-2026"
    assert kinds[landing] == "my_100"
    assert dests.index("2026-12-31") > quarter
    my_pages = [page for page in pages if page.kind == "my_100"]
    assert my_pages
    assert my_pages[0].dest == spec.my_100_dest
    assert _numbers(my_pages) == list(range(1, MY_100_COUNT + 1))


def test_my_100_then_checkoff_when_both_on():
    spec = Spec(my_100=True, checkoff_365=True, months=(1,), notes_pages=0)
    dests = [page.dest for page in YearPlanner().pages(spec)]
    annual = dests.index(spec.year_dest)
    landing = dests.index(spec.my_100_dest)
    checkoff = dests.index(spec.checkoff_365_dest)
    quarter = dests.index(spec.dest_for_quarter(1))
    assert dests[:2] == ["cover", spec.year_dest]
    assert annual < landing < checkoff < quarter
    assert dests[annual + 1] == spec.my_100_dest
    last_my = max(i for i, dest in enumerate(dests) if dest.startswith("my-100-"))
    assert last_my + 1 == checkoff


def test_my_100_page_and_strip():
    spec = _on()
    page = next(p for p in My100Section(spec).pages() if p.kind == "my_100")
    assert page.dest == "my-100-2026"
    assert page.title == "My 100"
    leaf = next(item for item in page.components if isinstance(item, My100Page))
    assert leaf.year == 2026
    assert leaf.dest == "my-100-2026"
    assert leaf.page == 1
    assert leaf.index_dest == spec.my_100_dest
    assert leaf.numbers[0] == 1
    assert strip_active(page.kind) == "100"
    assert ("100", spec.my_100_dest) in strip_items(page)
    assert strip_items(page) == (
        *_YEAR_STRIP[:8],
        ("100", spec.my_100_dest),
        *_YEAR_STRIP[8:],
    )


def test_my_100_grid_is_two_columns_from_the_well():
    assert MY_100_MAX_COLS == 2
    for device in (NOMAD, SCRIBE):
        well = well_rect(device)
        cols, row_n = my_100_grid(well)
        assert cols == 2
        assert row_n >= 1
        assert well.w >= cols * MY_100_MIN_COL_W + (cols - 1) * 3.0 - 1e-6
        assert well.h >= row_n * MY_100_MIN_ROW_H - 1e-6
        pages_n = my_100_page_count(well)
        assert pages_n >= 1
        seen: list[int] = []
        for page in range(1, pages_n + 1):
            seen.extend(my_100_page_numbers(well, page))
        assert seen == list(range(1, MY_100_COUNT + 1))


def test_my_100_nomad_is_two_col_pages_then_full_column():
    well = well_rect(NOMAD)
    cols, row_n = my_100_grid(well)
    cap = my_100_capacity(well)
    assert cols == 2
    assert row_n == 20
    assert cap == 40
    assert my_100_page_count(well) == 3
    assert my_100_page_numbers(well, 1) == tuple(range(1, 41))
    assert my_100_page_numbers(well, 2) == tuple(range(41, 81))
    last = my_100_page_numbers(well, 3)
    assert last == tuple(range(81, 101))
    assert len(last) == row_n
    tracks = my_100_columns(well)
    assert len(tracks) == 2
    assert tracks[0].w == pytest.approx(tracks[1].w)
    open_box = my_100_open_seat(well, len(last))
    assert open_box is not None
    assert open_box.x == pytest.approx(tracks[1].x)
    assert open_box.w == pytest.approx(tracks[1].w)
    assert open_box.h == pytest.approx(well.h)
    assert my_100_open_seat(well, cap) is None


def test_my_100_column_width_is_stable_across_pages():
    well = well_rect(NOMAD)
    tracks = my_100_columns(well)
    assert len(tracks) == MY_100_MAX_COLS
    assert tracks[0].w == pytest.approx(tracks[1].w)
    for page in range(1, my_100_page_count(well) + 1):
        assert my_100_columns(well)[0].w == pytest.approx(tracks[0].w)
        assert my_100_columns(well)[1].x == pytest.approx(tracks[1].x)


def test_my_100_cap_is_painter_constant_not_spec():
    assert MY_100_MAX_COLS == 2
    assert not hasattr(Spec(), "my_100_columns")
    assert not hasattr(Spec(), "my_100_pages")


def test_my_100_row_parts_number_writein_checkbox():
    row = Rect(4, 20, 34, 5.6)
    num, write, check = my_100_row_parts(row)
    assert num.w == pytest.approx(MY_100_NUM_W)
    assert check.w == pytest.approx(MY_100_CHECK)
    assert check.right == pytest.approx(row.right)
    assert num.right <= write.x
    assert write.right <= check.x
    assert write.w > MY_100_CHECK


def test_my_100_paint_numbers_checks_no_caption_or_local_title():
    spec = _on(months=(1,), notes_pages=0)
    pages = My100Section(spec).pages()
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    for page in pages:
        leaf = next(item for item in page.components if isinstance(item, My100Page))
        paint_my_100(plotter, well, leaf)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "My 100" not in texts
    assert not any("hundred" in t.lower() for t in texts)
    assert "1." in texts
    assert f"{MY_100_COUNT}." in texts
    assert [t for t in texts if t.endswith(".") and t[:-1].isdigit()] == [
        f"{n}." for n in range(1, MY_100_COUNT + 1)
    ]
    last = next(item for item in pages[-1].components if isinstance(item, My100Page))
    leftover = RecordingPlotter()
    paint_my_100(leftover, well, last)
    leftover_nums = [
        op[2]
        for op in leftover.ops
        if op[0] == "text" and str(op[2]).endswith(".") and str(op[2])[:-1].isdigit()
    ]
    rules = [
        op for op in leftover.ops if op[0] == "line" and op[5] == pytest.approx(0.12)
    ]
    frames = [
        op
        for op in leftover.ops
        if op[0] == "rect" and op[2] is True and op[3] is False
    ]
    assert leftover_nums == [f"{n}." for n in last.numbers]
    assert len(rules) == len(last.numbers)
    assert frames == []


def test_my_100_layout_header_title_once():
    spec = _on(months=(1,), notes_pages=1)
    page = My100Section(spec).pages()[0]
    plotter = RecordingPlotter()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("My 100") == 1
    assert "2026" in texts
    assert "Year" in texts
    assert "Quar" in texts
    assert "Task" in texts
    links = plotter.links()
    assert spec.year_dest in links
    assert spec.quarter_dest in links
    assert spec.tasks_index_dest in links


def test_my_100_scribe_uses_same_two_col_packer():
    nomad_pages = my_100_page_count(well_rect(NOMAD))
    scribe_pages = my_100_page_count(well_rect(SCRIBE))
    assert nomad_pages >= 1
    assert scribe_pages >= 1
    assert my_100_grid(well_rect(SCRIBE))[0] == 2
    scribe = Spec(device="kindle-scribe", my_100=True, months=(1,), notes_pages=0)
    pages = My100Section(scribe).pages()
    assert len(pages) == scribe_pages
    assert _numbers(pages) == list(range(1, MY_100_COUNT + 1))
    if scribe_pages > 1:
        assert pages[1].dest == scribe.dest_for_my_100(2)


def test_my_100_paginated_dests_and_chip():
    well = well_rect(NOMAD)
    pages_n = my_100_page_count(well)
    spec = _on(months=(1,), notes_pages=0)
    pages = My100Section(spec).pages()
    assert len(pages) == pages_n
    assert pages[0].dest == "my-100-2026"
    if pages_n > 1:
        assert pages[1].dest == "my-100-2026-02"
        leaf = next(item for item in pages[1].components if isinstance(item, My100Page))
        assert leaf.page == 2
        assert leaf.pages == pages_n
        assert leaf.index_dest == "my-100-2026"
        assert leaf.numbers[0] == my_100_page_numbers(well, 2)[0]
        assert dict(strip_items(pages[1]))["100"] == spec.my_100_dest
        assert strip_active(pages[1].kind) == "100"
    if pages_n > 2:
        assert pages[2].dest == "my-100-2026-03"


def test_my_100_presses_into_year_pdf(tmp_path: Path):
    spec = Spec(my_100=True, months=(1,), notes_pages=0)
    pages = YearPlanner().pages(spec)
    plotter = Fpdf2Plotter(NOMAD)
    plot_pages(
        lambda: pages,
        plotter,
        ramp=EffectiveRamp(),
        device=spec.device,
    )
    pdf = tmp_path / "my-100.pdf"
    plotter.finish(pdf)
    assert pdf.stat().st_size > 0
    dests = [page.dest for page in pages]
    assert dests.index(spec.my_100_dest) == dests.index(spec.year_dest) + 1


@pytest.mark.skipif(
    shutil.which("pdftoppm") is None, reason="pdftoppm (poppler-utils) required"
)
def test_my_100_png_proof(tmp_path: Path):
    spec = Spec(my_100=True, months=(1,), notes_pages=0)
    pages = YearPlanner().pages(spec)
    plotter = Fpdf2Plotter(NOMAD)
    plot_pages(
        lambda: pages,
        plotter,
        ramp=EffectiveRamp(),
        device=spec.device,
    )
    pdf = tmp_path / "my-100.pdf"
    plotter.finish(pdf)
    dests = [page.dest for page in pages]
    first = dests.index(spec.my_100_dest) + 1
    my_pages = [page for page in pages if page.kind == "my_100"]
    for offset, _page in enumerate(my_pages):
        dest = tmp_path / f"my-100-2026-{offset + 1:02d}.png"
        render_page_png(pdf, first + offset, dest)
        assert dest.stat().st_size > 0


def test_my_100_row_h_matches_full_grid():
    well = well_rect(NOMAD)
    _cols, row_n = my_100_grid(well)
    assert my_100_row_h(well) == pytest.approx(well.h / row_n)
