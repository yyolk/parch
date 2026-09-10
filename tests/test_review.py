from datetime import date

import pytest

from parch.books import YearPlanner
from parch.calendar import month_week_bands, short_date_range
from parch.components import ReviewsIndex, ReviewWeekPage
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    HAIR,
    REVIEW_INDEX_CHIP_GAP,
    REVIEW_INDEX_CHIP_H,
    REVIEW_INDEX_COL_GAP,
    REVIEW_INDEX_HEAD_H,
    REVIEW_INDEX_INSET_X,
    REVIEW_INDEX_INSET_Y,
    SOFT,
    TICK,
    paint_review,
    paint_reviews_index_months,
    reviews_index_chip_frame,
    reviews_index_chip_parts,
    reviews_index_chip_strip,
    reviews_index_columns,
    reviews_index_link_hits,
    reviews_index_month_seats,
    strip_active,
    strip_items,
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
    assert page.title == "Reviews"
    index = next(item for item in page.components if isinstance(item, ReviewsIndex))
    assert index.year == 2026
    assert index.quarter == 1
    assert index.dest == "reviews-index-2026-Q1"
    assert [column.month for column in index.columns] == [1, 2, 3]
    assert [column.name for column in index.columns] == ["January", "February", "March"]
    assert [len(column.weeks) for column in index.columns] == [5, 4, 5]
    assert index.columns[0].weeks[0].dest == "review-2026-W01"
    assert index.columns[0].weeks[-1].iso_week == 5
    assert index.columns[1].weeks[0].iso_week == 6
    assert index.columns[2].weeks[-1].iso_week == 14
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


def test_reviews_index_seats_month_columns():
    well = well_rect(NOMAD)
    counts = (5, 4, 5)
    cols = reviews_index_columns(well, len(counts))
    assert len(cols) == 3
    assert cols[0].x == pytest.approx(well.x)
    assert cols[0].y == pytest.approx(well.y)
    assert cols[0].h == pytest.approx(well.h)
    assert cols[-1].right == pytest.approx(well.right)
    assert all(col.y == pytest.approx(well.y) and col.h == pytest.approx(well.h) for col in cols)
    leftover = well.w - REVIEW_INDEX_COL_GAP * 2
    assert cols[0].w == pytest.approx(leftover / 3)
    assert cols[1].w == pytest.approx(leftover / 3)
    assert cols[2].w == pytest.approx(leftover / 3)
    assert cols[1].x == pytest.approx(cols[0].right + REVIEW_INDEX_COL_GAP)
    assert cols == columns(well, 3, gap=REVIEW_INDEX_COL_GAP)

    head, chips = reviews_index_month_seats(cols[0], 5, stack=5)
    assert head.h == pytest.approx(REVIEW_INDEX_HEAD_H)
    assert head.x > cols[0].x
    assert head.x == pytest.approx(cols[0].x + REVIEW_INDEX_INSET_X)
    assert len(chips) == 5
    assert chips[0].y > head.bottom
    assert chips[-1].bottom < cols[0].bottom
    assert chips[0].h > REVIEW_INDEX_CHIP_H
    assert chips[1].y == pytest.approx(chips[0].bottom + REVIEW_INDEX_CHIP_GAP)
    assert chips[0].w == pytest.approx(cols[0].w - 2 * REVIEW_INDEX_INSET_X)
    assert chips[-1].bottom == pytest.approx(
        cols[0].bottom - REVIEW_INDEX_INSET_Y, abs=0.05
    )
    stub, dated = reviews_index_chip_parts(chips[0])
    strip = reviews_index_chip_strip(chips[0])
    assert strip.h == pytest.approx(REVIEW_INDEX_CHIP_H)
    assert strip.y == pytest.approx(chips[0].y + (chips[0].h - strip.h) / 2, abs=0.05)
    assert stub.y == pytest.approx(strip.y)
    assert dated.y > stub.bottom
    assert dated.bottom <= chips[0].bottom
    frame = reviews_index_chip_frame(chips[0])
    assert frame.h < chips[0].h
    assert frame.y > chips[0].y
    assert frame.bottom < chips[0].bottom
    assert reviews_index_link_hits(chips[0]) == (frame,)

    shorter = reviews_index_month_seats(cols[1], 4, stack=5)[1]
    assert len(shorter) == 4
    assert shorter[0].h == pytest.approx(chips[0].h)
    assert shorter[-1].bottom < chips[-1].bottom


def test_reviews_index_paint_month_headers_and_week_links():
    spec = Spec(notes_pages=1, months=(1, 2, 3))
    page = next(p for p in ReviewSection(spec).pages() if p.kind == "reviews_index")
    index = next(item for item in page.components if isinstance(item, ReviewsIndex))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_reviews_index_months(plotter, well, index)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "January" in texts
    assert "February" in texts
    assert "March" in texts
    for week in range(1, 15):
        assert f"W{week:02d}" in texts
    assert "29 Dec–4 Jan" in texts
    assert short_date_range(date(2026, 1, 26), date(2026, 2, 1)) in texts
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
        "P",
    ):
        assert rejected not in texts

    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert ticks == []

    links = [op[2] for op in plotter.ops if op[0] == "link"]
    assert links == [f"review-2026-W{week:02d}" for week in range(1, 15)]
    stack = max(len(column.weeks) for column in index.columns)
    seats = [
        chip
        for col_box, column in zip(
            reviews_index_columns(well, len(index.columns)), index.columns, strict=True
        )
        for chip in reviews_index_month_seats(col_box, len(column.weeks), stack=stack)[1]
    ]
    expected_hits: list[tuple[Rect, str]] = []
    for seat, dest in zip(
        seats, [f"review-2026-W{week:02d}" for week in range(1, 15)], strict=True
    ):
        hits = reviews_index_link_hits(seat)
        assert hits == (reviews_index_chip_frame(seat),)
        expected_hits.extend((hit, dest) for hit in hits)
    assert [(op[1], op[2]) for op in plotter.ops if op[0] == "link"] == expected_hits

    frames = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[4] == pytest.approx(HAIR)
    ]
    cols = reviews_index_columns(well, 3)
    chip_frames = [reviews_index_chip_frame(seat) for seat in seats]
    assert [op[1] for op in frames if op[1].h == pytest.approx(well.h)] == list(cols)
    assert [op[1] for op in frames if op[1] in chip_frames] == chip_frames
    assert all(op[6] == pytest.approx(SOFT) for op in frames)


def test_review_paint_notes_stub():
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
    assert texts.count("Review") == 0
    assert texts.count("Notes") == 0
    assert "Agenda" not in texts
    assert "Action items" not in texts
    assert "Todo" not in texts
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert ticks == []
    outline = next(op for op in plotter.ops if op[0] == "rect" and op[1] == well)
    assert outline[2] is True
    hlines = [op for op in plotter.ops if op[0] == "line"]
    assert len(hlines) > 8


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
    assert "29 Dec–4 Jan" not in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Proj", "Meet", "Rev", "Week", "Day", "Notes"):
        assert label in texts
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
    assert "Reviews" in texts
    assert "Q1" in texts
    assert "January" in texts
    assert "Rev" in texts
    assert strip_active(page.kind) == "Rev"
    assert dict(strip_items(page))["Rev"] == spec.reviews_index_dest


def test_q1_columns_match_calendar():
    spec = Spec(months=(1, 2, 3))
    index = next(
        item
        for page in ReviewSection(spec).pages()
        if page.kind == "reviews_index"
        for item in page.components
        if isinstance(item, ReviewsIndex)
    )
    calendar = month_week_bands(2026, (1, 2, 3), weekday_start=0)
    assert [len(column.weeks) for column in index.columns] == [
        len(weeks) for _month, weeks in calendar
    ]
    assert index.columns[0].weeks[0].monday == calendar[0][1][0][0]
