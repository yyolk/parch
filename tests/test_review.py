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
    REVIEW_GAP,
    REVIEW_INDEX_LINE_H,
    REVIEW_INDEX_WEEK_W,
    REVIEW_NEXT_ROWS,
    TICK,
    checklist_content_height,
    paint_review,
    paint_reviews_index,
    review_notes_height,
    review_seats,
    reviews_index_link_hits,
    reviews_index_rows,
    reviews_index_week_parts,
    reviews_index_week_strip,
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


def test_review_not_in_year_planner():
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
    index = next(item for item in page.components if isinstance(item, ReviewsIndex))
    assert index.year == 2026
    assert index.quarter == 1
    assert index.dest == "reviews-index-2026-Q1"
    assert [week.iso_week for week in index.weeks] == list(range(1, 15))
    assert index.weeks[0].dest == "review-2026-W01"
    assert index.weeks[-1].iso_week == 14
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


def test_review_section_order_indexes_then_weeks():
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


def test_review_dest_seats_stacked_bands():
    well = well_rect(NOMAD)
    wins, lessons, nxt, notes = review_seats(well)
    assert wins.y == pytest.approx(well.y)
    assert wins.x == pytest.approx(well.x)
    assert wins.w == pytest.approx(well.w)
    assert lessons.y == pytest.approx(wins.bottom + REVIEW_GAP)
    assert nxt.y == pytest.approx(lessons.bottom + REVIEW_GAP)
    assert nxt.h == pytest.approx(checklist_content_height(REVIEW_NEXT_ROWS))
    assert notes.y == pytest.approx(nxt.bottom + REVIEW_GAP)
    assert notes.bottom == pytest.approx(well.bottom)
    assert notes.h == pytest.approx(review_notes_height())
    assert wins.h == pytest.approx(lessons.h)
    assert wins.h > notes.h
    assert lessons.h > notes.h
    assert notes.h < nxt.h
    via = rows(
        well,
        4,
        gap=REVIEW_GAP,
        weights=(wins.h, lessons.h, nxt.h, notes.h),
    )
    for got, expected in zip((wins, lessons, nxt, notes), via, strict=True):
        assert got.x == pytest.approx(expected.x)
        assert got.y == pytest.approx(expected.y)
        assert got.w == pytest.approx(expected.w)
        assert got.h == pytest.approx(expected.h)


def test_reviews_index_seats():
    well = well_rect(NOMAD)
    seats = reviews_index_rows(well, 14)
    assert len(seats) == 14
    assert seats[0].y == pytest.approx(well.y)
    assert seats[-1].bottom == pytest.approx(well.bottom)
    stub, dated = reviews_index_week_parts(seats[0])
    strip = reviews_index_week_strip(seats[0])
    assert strip.h == pytest.approx(REVIEW_INDEX_LINE_H)
    assert stub.w == pytest.approx(REVIEW_INDEX_WEEK_W)
    assert dated.x == pytest.approx(stub.right)
    assert dated.right == pytest.approx(seats[0].right)
    via = columns(
        strip, 2, gap=0, weights=(REVIEW_INDEX_WEEK_W, max(strip.w - REVIEW_INDEX_WEEK_W, 1))
    )
    assert (stub, dated) == via
    assert reviews_index_link_hits(seats[0]) == (stub, dated)


def test_reviews_index_paint_week_links():
    spec = Spec(notes_pages=1, months=(1, 2, 3))
    page = next(p for p in ReviewSection(spec).pages() if p.kind == "reviews_index")
    index = next(item for item in page.components if isinstance(item, ReviewsIndex))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_reviews_index(plotter, well, index)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
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
    assert links == [dest for week in range(1, 15) for dest in (f"review-2026-W{week:02d}",) * 2]
    seats = reviews_index_rows(well, 14)
    expected_hits: list[tuple[Rect, str]] = []
    for seat, dest in zip(
        seats, [f"review-2026-W{week:02d}" for week in range(1, 15)], strict=True
    ):
        expected_hits.extend((hit, dest) for hit in reviews_index_link_hits(seat))
    assert [(op[1], op[2]) for op in plotter.ops if op[0] == "link"] == expected_hits


def test_review_paint_stacked_bands():
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
    assert texts.count("Wins") == 1
    assert texts.count("Lessons") == 1
    assert texts.count("Next week") == 1
    assert texts.count("Notes") == 1
    assert texts.count("Review") == 0
    assert "Agenda" not in texts
    assert "Action items" not in texts
    assert "Todo" not in texts
    assert "Doing" not in texts
    assert "Done" not in texts
    assert "Active" not in texts
    assert "Waiting" not in texts
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == REVIEW_NEXT_ROWS
    wins, _lessons, nxt, _notes = review_seats(well)
    assert all(nxt.y <= op[1].y <= nxt.bottom for op in ticks)
    assert all(op[1].y > wins.bottom for op in ticks)


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
    assert "Rev" in texts
    assert strip_active(page.kind) == "Rev"
    assert dict(strip_items(page))["Rev"] == spec.reviews_index_dest


def test_q1_weeks_match_calendar():
    spec = Spec(months=(1, 2, 3))
    index = next(
        item
        for page in ReviewSection(spec).pages()
        if page.kind == "reviews_index"
        for item in page.components
        if isinstance(item, ReviewsIndex)
    )
    calendar = month_week_bands(2026, (1, 2, 3), weekday_start=0)
    flat = [week for _month, weeks in calendar for week in weeks]
    assert len(index.weeks) == len(flat)
    assert index.weeks[0].monday == flat[0][0]
    assert index.weeks[-1].iso_week == 14
