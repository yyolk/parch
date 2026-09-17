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
    MY_100_CAPTION_LINES,
    MY_100_CHECK,
    MY_100_COUNT,
    MY_100_MIN_COL_W,
    MY_100_MIN_ROW_H,
    MY_100_NUM_W,
    MY_100_TITLE,
    my_100_grid,
    my_100_head_seats,
    my_100_page_count,
    my_100_page_numbers,
    my_100_row_parts,
    my_100_seats,
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
    numbers = [
        n
        for page in my_pages
        for item in page.components
        if isinstance(item, My100Page)
        for n in item.numbers
    ]
    assert numbers == list(range(1, MY_100_COUNT + 1))


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
    assert strip_active(page.kind) == "Year"
    assert strip_items(page) == _YEAR_STRIP
    assert all(label != "100" for label, _ in strip_items(page))


def test_my_100_grid_fits_device_well():
    for device in (NOMAD, SCRIBE):
        well = well_rect(device)
        head, list_box = my_100_seats(well)
        assert head.bottom + 2.8 == pytest.approx(list_box.y)
        cols, row_n = my_100_grid(list_box)
        assert cols >= 2
        assert row_n >= 1
        assert list_box.w >= cols * MY_100_MIN_COL_W + (cols - 1) * 3.0 - 1e-6
        assert list_box.h >= row_n * MY_100_MIN_ROW_H - 1e-6
        pages_n = my_100_page_count(well)
        assert pages_n >= 1
        seen: list[int] = []
        for page in range(1, pages_n + 1):
            seen.extend(my_100_page_numbers(well, page))
        assert seen == list(range(1, MY_100_COUNT + 1))
        title, caption = my_100_head_seats(head)
        assert title.w == pytest.approx(24.0)
        assert caption.x == pytest.approx(title.right)


def test_my_100_last_page_shrinks_empty_columns():
    well = well_rect(NOMAD)
    pages_n = my_100_page_count(well)
    assert pages_n >= 1
    _head, list_box = my_100_seats(well)
    full_cols, full_rows = my_100_grid(list_box)
    last = my_100_page_numbers(well, pages_n)
    last_cols, last_rows = my_100_grid(list_box, entries=len(last))
    assert last_cols * last_rows >= len(last)
    assert last_cols <= full_cols
    assert last_rows <= full_rows
    if len(last) <= full_rows:
        assert last_cols == 1 or last_cols * last_rows == len(last)


def test_my_100_row_parts_number_writein_checkbox():
    row = Rect(4, 20, 34, 5.6)
    num, write, check = my_100_row_parts(row)
    assert num.w == pytest.approx(MY_100_NUM_W)
    assert check.w == pytest.approx(MY_100_CHECK)
    assert check.right == pytest.approx(row.right)
    assert num.right <= write.x
    assert write.right <= check.x
    assert write.w > MY_100_CHECK


def test_my_100_paint_title_caption_numbers_and_checks():
    spec = _on(months=(1,), notes_pages=0)
    pages = My100Section(spec).pages()
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    for page in pages:
        leaf = next(item for item in page.components if isinstance(item, My100Page))
        paint_my_100(plotter, well, leaf)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count(MY_100_TITLE) == len(pages)
    for line in MY_100_CAPTION_LINES:
        assert line in texts
    assert "1." in texts
    assert f"{MY_100_COUNT}." in texts
    assert [t for t in texts if t.endswith(".") and t[:-1].isdigit()] == [
        f"{n}." for n in range(1, MY_100_COUNT + 1)
    ]
    rules = [
        op for op in plotter.ops if op[0] == "line" and op[5] == pytest.approx(0.12)
    ]
    assert len(rules) == MY_100_COUNT


def test_my_100_layout_header_and_year_strip():
    spec = _on(months=(1,), notes_pages=1)
    page = My100Section(spec).pages()[0]
    plotter = RecordingPlotter()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "My 100" in texts
    assert "2026" in texts
    assert "Year" in texts
    assert "Quar" in texts
    assert "Task" in texts
    links = plotter.links()
    assert spec.year_dest in links
    assert spec.quarter_dest in links
    assert spec.tasks_index_dest in links


def test_my_100_scribe_uses_same_packer_not_a_scribe_grid():
    nomad_pages = my_100_page_count(well_rect(NOMAD))
    scribe_pages = my_100_page_count(well_rect(SCRIBE))
    assert nomad_pages >= 1
    assert scribe_pages >= 1
    scribe = Spec(device="kindle-scribe", my_100=True, months=(1,), notes_pages=0)
    pages = My100Section(scribe).pages()
    assert len(pages) == scribe_pages
    numbers = [
        n
        for page in pages
        for item in page.components
        if isinstance(item, My100Page)
        for n in item.numbers
    ]
    assert numbers == list(range(1, MY_100_COUNT + 1))
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
    dest = tmp_path / "my-100-2026.png"
    render_page_png(pdf, first, dest)
    assert dest.is_file()
    assert dest.stat().st_size > 0
    my_pages = [page for page in pages if page.kind == "my_100"]
    if len(my_pages) > 1:
        dest2 = tmp_path / "my-100-2026-02.png"
        render_page_png(pdf, first + 1, dest2)
        assert dest2.stat().st_size > 0
