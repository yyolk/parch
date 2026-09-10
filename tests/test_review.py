from datetime import date

import pytest

from parch.books import YearPlanner
from parch.calendar import month_week_bands, short_date_range
from parch.components import ReviewIndex, ReviewWeekPage
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    FOCUS_LABEL_H,
    FOCUS_PAD_BOT,
    FOCUS_PAD_MID,
    FOCUS_PAD_TOP,
    FOCUS_PITCH,
    REVIEW_COL_GAP,
    REVIEW_LABELS,
    TICK,
    paint_review,
    paint_review_index_months,
    review_row_count,
    review_seats,
    strip_active,
    strip_items,
    tasks_index_band_seats,
    tasks_index_bands,
    tasks_index_link_hits,
    tasks_index_week_parts,
)
from parch.plotter import RecordingPlotter
from parch.sections.review import ReviewSection
from parch.spec import Spec
from parch.tracks import columns


def _rects_overlap(a: Rect, b: Rect) -> bool:
    return a.x < b.right and b.x < a.right and a.y < b.bottom and b.y < a.bottom


_REV_STRIP = (
    ("Year", "year-2026"),
    ("Quar", "quarter-2026-Q1"),
    ("Mon", "month-2026-01"),
    ("Habit", "month-2026-01-habits"),
    ("Proj", "projects-index-2026-01"),
    ("Meet", "meetings-index-2026"),
    ("Rev", "review-index-2026-Q1"),
    ("Week", "week-2026-W01"),
    ("Day", "2026-01-01"),
    ("Notes", "2026-01-01-notes-1"),
)


def test_review_not_in_year_planner():
    spec = Spec(notes_pages=1)
    dests = [page.dest for page in YearPlanner().pages(spec)]
    assert dests[12] == "meetings-index-2026"
    assert dests[29] == "quarter-2026-Q1"
    assert not any(dest.startswith("review-") for dest in dests)
    year = next(page for page in YearPlanner().pages(spec) if page.kind == "annual")
    labels = [label for label, _ in strip_items(year)]
    assert "Rev" not in labels
    assert labels == ["Year", "Quar", "Mon", "Habit", "Proj", "Meet", "Week", "Day", "Notes"]


def test_review_index_page():
    spec = Spec(notes_pages=1, months=(1, 2, 3))
    page = next(p for p in ReviewSection(spec).pages() if p.kind == "review_index")
    assert page.dest == "review-index-2026-Q1"
    assert page.title == "Review"
    index = next(item for item in page.components if isinstance(item, ReviewIndex))
    assert index.year == 2026
    assert index.quarter == 1
    assert index.dest == "review-index-2026-Q1"
    assert [band.month for band in index.bands] == [1, 2, 3]
    assert [band.name for band in index.bands] == ["January", "February", "March"]
    assert [len(band.weeks) for band in index.bands] == [5, 4, 5]
    assert index.bands[0].weeks[0].dest == "review-2026-W01"
    assert index.bands[0].weeks[-1].iso_week == 5
    assert index.bands[1].weeks[0].iso_week == 6
    assert index.bands[2].weeks[-1].iso_week == 14
    assert strip_active(page.kind) == "Rev"
    assert strip_items(page) == _REV_STRIP


def test_review_dest_page():
    spec = Spec(notes_pages=1, months=(1, 2, 3))
    page = next(p for p in ReviewSection(spec).pages() if p.dest == "review-2026-W01")
    assert page.kind == "review"
    assert page.title == "Review"
    dest = next(item for item in page.components if isinstance(item, ReviewWeekPage))
    assert dest.year == 2026
    assert dest.iso_year == 2026
    assert dest.iso_week == 1
    assert dest.monday == date(2025, 12, 29)
    assert dest.sunday == date(2026, 1, 4)
    assert dest.index_dest == "review-index-2026-Q1"
    assert strip_active(page.kind) == "Rev"
    assert strip_items(page) == _REV_STRIP
    assert ("Rev", "review-index-2026-Q1") in strip_items(page)
    assert ("Week", "week-2026-W01") in strip_items(page)
    assert "Task" not in dict(strip_items(page))


def test_review_section_order_indexes_then_weeks():
    spec = Spec(notes_pages=1)
    dests = [page.dest for page in ReviewSection(spec).pages()]
    assert dests[0] == "review-index-2026-Q1"
    assert dests[1:15] == [f"review-2026-W{week:02d}" for week in range(1, 15)]
    assert dests[15] == "review-index-2026-Q2"
    assert dests.count("review-index-2026-Q1") == 1
    assert dests.count("review-index-2026-Q4") == 1
    assert [page.kind for page in ReviewSection(spec).pages()].count("review_index") == 4
    assert [page.kind for page in ReviewSection(spec).pages()].count("review") == 53
    week_dests = [dest for dest in dests if dest.startswith("review-2026-W")]
    assert week_dests == [f"review-2026-W{week:02d}" for week in range(1, 54)]
    assert len(week_dests) == len(set(week_dests))
    july = next(p for p in ReviewSection(spec).pages() if p.dest == "review-2026-W29")
    well = next(item for item in july.components if isinstance(item, ReviewWeekPage))
    assert well.index_dest == "review-index-2026-Q3"
    assert dict(strip_items(july))["Rev"] == "review-index-2026-Q3"
    assert dict(strip_items(july))["Quar"] == "quarter-2026-Q3"


def test_review_dest_seats_use_tracks_columns():
    well = well_rect(NOMAD)
    seats = review_seats(well)
    assert seats == columns(well, 3, gap=REVIEW_COL_GAP)
    assert len(seats) == 3
    assert REVIEW_COL_GAP == pytest.approx(2.6)
    assert seats[0].y == pytest.approx(well.y)
    assert seats[0].h == pytest.approx(well.h)
    assert seats[0].x == pytest.approx(well.x)
    assert seats[-1].right == pytest.approx(well.right)
    assert seats[-1].bottom == pytest.approx(well.bottom)
    leftover = well.w - REVIEW_COL_GAP * 2
    assert all(col.w == pytest.approx(leftover / 3) for col in seats)
    assert seats[1].x == pytest.approx(seats[0].right + REVIEW_COL_GAP)
    assert seats[2].x == pytest.approx(seats[1].right + REVIEW_COL_GAP)


def test_review_dest_row_count_fills_column():
    well = well_rect(NOMAD)
    col = review_seats(well)[0]
    n = review_row_count(col)
    usable = col.h - FOCUS_PAD_TOP - FOCUS_LABEL_H - FOCUS_PAD_MID - FOCUS_PAD_BOT
    expected = max(1, int((usable - TICK) / FOCUS_PITCH) + 1)
    assert n == expected
    assert n == 25
    assert n > 8


def test_review_index_paint_month_headers_and_week_links():
    spec = Spec(notes_pages=1, months=(1, 2, 3))
    page = next(p for p in ReviewSection(spec).pages() if p.kind == "review_index")
    index = next(item for item in page.components if isinstance(item, ReviewIndex))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_review_index_months(plotter, well, index)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "January" in texts
    assert "February" in texts
    assert "March" in texts
    for week in range(1, 15):
        assert f"W{week:02d}" in texts
    assert "29 Dec–4 Jan" in texts
    assert short_date_range(date(2026, 1, 26), date(2026, 2, 1)) in texts
    assert "Review" not in texts
    for rejected in (
        "Went well",
        "To improve",
        "Focus next",
        "Todo",
        "Doing",
        "Done",
        "Notes",
    ):
        assert rejected not in texts

    links = [op[2] for op in plotter.ops if op[0] == "link"]
    assert links == [dest for week in range(1, 15) for dest in (f"review-2026-W{week:02d}",) * 2]
    counts = tuple(len(band.weeks) for band in index.bands)
    seats = [
        row
        for band_box, band in zip(tasks_index_bands(well, counts), index.bands, strict=True)
        for row in tasks_index_band_seats(band_box, len(band.weeks))[1]
    ]
    expected_hits: list[tuple[Rect, str]] = []
    for seat, dest in zip(
        seats, [f"review-2026-W{week:02d}" for week in range(1, 15)], strict=True
    ):
        stub, dated, write = tasks_index_week_parts(seat)
        hits = tasks_index_link_hits(seat)
        assert hits == (stub, dated)
        assert not any(_rects_overlap(hit, write) for hit in hits)
        expected_hits.extend((hit, dest) for hit in hits)
    assert [(op[1], op[2]) for op in plotter.ops if op[0] == "link"] == expected_hits


def test_review_paint_three_columns_no_review_caption():
    dest = ReviewWeekPage(
        year=2026,
        iso_year=2026,
        iso_week=1,
        monday=date(2025, 12, 29),
        sunday=date(2026, 1, 4),
        index_dest="review-index-2026-Q1",
    )
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_review(plotter, well, dest)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts == list(REVIEW_LABELS)
    assert "Review" not in texts
    assert "Notes" not in texts
    assert "Went well" in texts
    assert "To improve" in texts
    assert "Focus next" in texts
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    per = review_row_count(review_seats(well)[0])
    assert len(ticks) == per * 3
    outlines = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(review_seats(well)[0].w)
    ]
    assert [op[1] for op in outlines] == list(review_seats(well))


def test_review_header_week_chip_and_rev_tab():
    spec = Spec(notes_pages=1, months=(1, 2, 3))
    page = next(p for p in ReviewSection(spec).pages() if p.dest == "review-2026-W01")
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("Review") == 1
    assert "W01" in texts
    assert "2026" in texts
    assert "Went well" in texts
    assert "To improve" in texts
    assert "Focus next" in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Proj", "Meet", "Rev", "Week", "Day", "Notes"):
        assert label in texts
    assert "Task" not in texts
    assert strip_active(page.kind) == "Rev"
    links = [op[2] for op in plotter.ops if op[0] == "link"]
    assert links.count("review-index-2026-Q1") >= 2
    chip = next(op[1] for op in plotter.ops if op[0] == "text" and op[2] == "W01")
    assert any(
        op[0] == "link" and op[2] == "review-index-2026-Q1" and _rects_overlap(op[1], chip)
        for op in plotter.ops
    )


def test_review_index_chrome_rev_tab():
    spec = Spec(notes_pages=1, months=(1, 2, 3))
    page = next(p for p in ReviewSection(spec).pages() if p.kind == "review_index")
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Review" in texts
    assert "Q1" in texts
    assert "January" in texts
    assert "Rev" in texts
    assert strip_active(page.kind) == "Rev"
    assert dict(strip_items(page))["Rev"] == spec.review_index_dest


def test_q1_review_bands_match_calendar():
    spec = Spec(months=(1, 2, 3))
    index = next(
        item
        for page in ReviewSection(spec).pages()
        if page.kind == "review_index"
        for item in page.components
        if isinstance(item, ReviewIndex)
    )
    calendar = month_week_bands(2026, (1, 2, 3), weekday_start=0)
    assert [len(band.weeks) for band in index.bands] == [len(weeks) for _month, weeks in calendar]
    assert index.bands[0].weeks[0].monday == calendar[0][1][0][0]
