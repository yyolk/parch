from datetime import date

import pytest

from parch.books import YearPlanner
from parch.calendar import month_week_bands
from parch.components import ReviewIndex, ReviewWeekPage
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    REVIEW_INDEX_BAND_GAP,
    REVIEW_INDEX_CHIP_GAP,
    REVIEW_INDEX_CHIP_H,
    REVIEW_INDEX_CHIP_W,
    REVIEW_INDEX_HEAD_H,
    paint_review,
    paint_reviews_index_months,
    review_chip_range,
    review_index_band_seats,
    review_index_bands,
    review_index_chip_row,
    review_index_chip_strip,
    review_index_link_hits,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.sections.review import ReviewSection
from parch.spec import Spec
from parch.tracks import columns, rows


def _rects_overlap(a: Rect, b: Rect) -> bool:
    return a.x < b.right and b.x < a.right and a.y < b.bottom and b.y < a.bottom


_REV_STRIP = (
    ("Year", "year-2026"),
    ("Quar", "quarter-2026-Q1"),
    ("Mon", "month-2026-01"),
    ("Habit", "month-2026-01-habits"),
    ("Proj", "projects-index-2026-01"),
    ("Meet", "meetings-index-2026"),
    ("Rev", "reviews-index-2026-Q1"),
    ("Week", "week-2026-W01"),
    ("Day", "2026-01-01"),
    ("Notes", "2026-01-01-notes-1"),
)


def test_reviews_not_in_year_planner():
    spec = Spec(notes_pages=1)
    dests = [page.dest for page in YearPlanner().pages(spec)]
    assert dests[12] == "meetings-index-2026"
    assert dests[29] == "quarter-2026-Q1"
    assert not any(dest.startswith("review") for dest in dests)
    year = next(page for page in YearPlanner().pages(spec) if page.kind == "annual")
    labels = [label for label, _ in strip_items(year)]
    assert "Rev" not in labels
    assert labels == ["Year", "Quar", "Mon", "Habit", "Proj", "Meet", "Week", "Day", "Notes"]


def test_reviews_index_page():
    spec = Spec(notes_pages=1, months=(1, 2, 3))
    page = next(p for p in ReviewSection(spec).pages() if p.kind == "reviews_index")
    assert page.dest == "reviews-index-2026-Q1"
    assert page.title == "Review"
    index = next(item for item in page.components if isinstance(item, ReviewIndex))
    assert index.year == 2026
    assert index.quarter == 1
    assert index.dest == "reviews-index-2026-Q1"
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
    assert dest.index_dest == "reviews-index-2026-Q1"
    assert strip_active(page.kind) == "Rev"
    assert strip_items(page) == _REV_STRIP
    assert ("Rev", "reviews-index-2026-Q1") in strip_items(page)
    assert ("Week", "week-2026-W01") in strip_items(page)


def test_reviews_section_order_indexes_then_weeks():
    spec = Spec(notes_pages=1)
    dests = [page.dest for page in ReviewSection(spec).pages()]
    assert dests[0] == "reviews-index-2026-Q1"
    assert dests[1:15] == [f"review-2026-W{week:02d}" for week in range(1, 15)]
    assert dests[15] == "reviews-index-2026-Q2"
    assert dests.count("reviews-index-2026-Q1") == 1
    assert dests.count("reviews-index-2026-Q4") == 1
    assert [page.kind for page in ReviewSection(spec).pages()].count("reviews_index") == 4
    assert [page.kind for page in ReviewSection(spec).pages()].count("review") == 53
    week_dests = [dest for dest in dests if dest.startswith("review-2026-W")]
    assert week_dests == [f"review-2026-W{week:02d}" for week in range(1, 54)]
    assert len(week_dests) == len(set(week_dests))
    july = next(p for p in ReviewSection(spec).pages() if p.dest == "review-2026-W29")
    well = next(item for item in july.components if isinstance(item, ReviewWeekPage))
    assert well.index_dest == "reviews-index-2026-Q3"
    assert dict(strip_items(july))["Rev"] == "reviews-index-2026-Q3"
    assert dict(strip_items(july))["Quar"] == "quarter-2026-Q3"


def test_reviews_index_seats_equal_month_bands_and_week_columns():
    well = well_rect(NOMAD)
    bands = review_index_bands(well, 3)
    assert len(bands) == 3
    assert bands[0].y == pytest.approx(well.y)
    assert bands[0].x == pytest.approx(well.x)
    assert bands[0].w == pytest.approx(well.w)
    assert bands[-1].bottom == pytest.approx(well.bottom)
    leftover = well.h - REVIEW_INDEX_BAND_GAP * 2
    assert bands[0].h == pytest.approx(leftover / 3)
    assert bands[1].h == pytest.approx(leftover / 3)
    assert bands[2].h == pytest.approx(leftover / 3)
    assert bands[1].y == pytest.approx(bands[0].bottom + REVIEW_INDEX_BAND_GAP)
    assert bands == rows(well, 3, gap=REVIEW_INDEX_BAND_GAP)

    head, chips = review_index_band_seats(bands[0], 5)
    assert head.h == pytest.approx(REVIEW_INDEX_HEAD_H)
    assert head.x > bands[0].x
    assert len(chips) == 5
    assert chips[0].y == pytest.approx(chips[-1].y)
    assert chips[0].h == pytest.approx(REVIEW_INDEX_CHIP_H)
    assert chips[0].w == pytest.approx(REVIEW_INDEX_CHIP_W)
    assert chips[0].y > head.bottom
    assert chips[1].x > chips[0].right
    strip = review_index_chip_strip(bands[0])
    assert chips == review_index_chip_row(strip, 5)
    packed_w = 5 * REVIEW_INDEX_CHIP_W + 4 * REVIEW_INDEX_CHIP_GAP
    packed = Rect(strip.x + (strip.w - packed_w) / 2, strip.y, packed_w, strip.h)
    assert chips == columns(packed, 5, gap=REVIEW_INDEX_CHIP_GAP)
    assert chips[0].x > strip.x
    assert chips[-1].right < strip.right
    assert review_index_link_hits(chips[0]) == (chips[0],)
    feb_head, feb_chips = review_index_band_seats(bands[1], 4)
    assert feb_head.h == pytest.approx(REVIEW_INDEX_HEAD_H)
    assert len(feb_chips) == 4
    assert feb_chips[0].w == pytest.approx(chips[0].w)


def test_review_chip_range_splits_cross_month_weeks():
    assert review_chip_range(date(2026, 1, 5), date(2026, 1, 11)) == ("5–11",)
    assert review_chip_range(date(2025, 12, 29), date(2026, 1, 4)) == ("29 Dec", "4 Jan")


def test_reviews_index_paint_month_headers_and_week_chip_links():
    spec = Spec(notes_pages=1, months=(1, 2, 3))
    page = next(p for p in ReviewSection(spec).pages() if p.kind == "reviews_index")
    index = next(item for item in page.components if isinstance(item, ReviewIndex))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_reviews_index_months(plotter, well, index)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "January" in texts
    assert "February" in texts
    assert "March" in texts
    for week in range(1, 15):
        assert f"W{week:02d}" in texts
    assert "29 Dec" in texts
    assert "4 Jan" in texts
    assert "5–11" in texts
    for rejected in (
        "Todo",
        "Doing",
        "Done",
        "Active",
        "Waiting",
        "This week",
        "Next week",
        "Later",
        "Agenda",
        "Attendees",
        "Wins",
        "Lessons",
        "P",
    ):
        assert rejected not in texts

    links = [op[2] for op in plotter.ops if op[0] == "link"]
    assert links == [f"review-2026-W{week:02d}" for week in range(1, 15)]
    seats = [
        chip
        for band_box, band in zip(review_index_bands(well, len(index.bands)), index.bands, strict=True)
        for chip in review_index_band_seats(band_box, len(band.weeks))[1]
    ]
    expected_hits = [(chip, f"review-2026-W{week:02d}") for week, chip in enumerate(seats, start=1)]
    assert [(op[1], op[2]) for op in plotter.ops if op[0] == "link"] == expected_hits
    for chip in seats:
        assert review_index_link_hits(chip) == (chip,)

    frames = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1] in seats
    ]
    assert len(frames) == 14


def test_review_paint_thin_notes_stub():
    dest = ReviewWeekPage(
        year=2026,
        iso_year=2026,
        iso_week=1,
        monday=date(2025, 12, 29),
        sunday=date(2026, 1, 4),
        index_dest="reviews-index-2026-Q1",
    )
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_review(plotter, well, dest)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("Notes") == 1
    assert texts.count("Review") == 0
    assert "Wins" not in texts
    assert "Lessons" not in texts
    assert "Agenda" not in texts
    assert "Todo" not in texts


def test_review_header_week_chip_and_rev_tab():
    spec = Spec(notes_pages=1, months=(1, 2, 3))
    page = next(p for p in ReviewSection(spec).pages() if p.dest == "review-2026-W01")
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Review" in texts
    assert "W01" in texts
    assert "2026" in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Proj", "Meet", "Rev", "Week", "Day", "Notes"):
        assert label in texts
    assert "Task" not in texts
    assert strip_active(page.kind) == "Rev"
    links = [op[2] for op in plotter.ops if op[0] == "link"]
    assert links.count("reviews-index-2026-Q1") >= 2
    chip = next(op[1] for op in plotter.ops if op[0] == "text" and op[2] == "W01")
    assert any(
        op[0] == "link" and op[2] == "reviews-index-2026-Q1" and _rects_overlap(op[1], chip)
        for op in plotter.ops
    )


def test_reviews_index_chrome_rev_tab():
    spec = Spec(notes_pages=1, months=(1, 2, 3))
    page = next(p for p in ReviewSection(spec).pages() if p.kind == "reviews_index")
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Review" in texts
    assert "Q1" in texts
    assert "January" in texts
    assert "Rev" in texts
    assert strip_active(page.kind) == "Rev"
    assert dict(strip_items(page))["Rev"] == spec.reviews_index_dest


def test_q1_review_bands_match_calendar():
    spec = Spec(months=(1, 2, 3))
    index = next(
        item
        for page in ReviewSection(spec).pages()
        if page.kind == "reviews_index"
        for item in page.components
        if isinstance(item, ReviewIndex)
    )
    calendar = month_week_bands(2026, (1, 2, 3), weekday_start=0)
    assert [len(band.weeks) for band in index.bands] == [len(weeks) for _month, weeks in calendar]
    assert index.bands[0].weeks[0].monday == calendar[0][1][0][0]
