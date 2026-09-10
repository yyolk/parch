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
    RULE,
    RULE_C,
    REVIEW_DAY_GAP,
    REVIEW_GAP,
    REVIEW_INDEX_GAP,
    REVIEW_INDEX_WEEK_W,
    REVIEW_STRIP_H,
    paint_review,
    paint_reviews_index,
    review_day_cues,
    review_day_link_hits,
    review_day_parts,
    review_seats,
    reviews_index_link_hits,
    reviews_index_rows,
    reviews_index_week_parts,
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
    assert page.title == "Review"
    index = next(item for item in page.components if isinstance(item, ReviewIndex))
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
    assert [day.weekday_label for day in dest.days] == [
        "Mon",
        "Tue",
        "Wed",
        "Thu",
        "Fri",
        "Sat",
        "Sun",
    ]
    assert [day.day.day for day in dest.days] == [29, 30, 31, 1, 2, 3, 4]
    assert dest.days[0].dest is None
    assert dest.days[3].dest == "2026-01-01"
    assert dest.days[6].dest == "2026-01-04"
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


def test_review_dest_seats_use_tracks():
    well = well_rect(NOMAD)
    strip, notes = review_seats(well)
    assert strip.y == pytest.approx(well.y)
    assert strip.h == pytest.approx(REVIEW_STRIP_H)
    assert strip.w == pytest.approx(well.w)
    assert notes.y == pytest.approx(strip.bottom + REVIEW_GAP)
    assert notes.bottom == pytest.approx(well.bottom)
    assert notes.h > strip.h
    assert notes.h > well.h * 0.7

    cues = review_day_cues(strip)
    assert len(cues) == 7
    assert cues[0].x == pytest.approx(strip.x)
    assert cues[-1].right == pytest.approx(strip.right)
    via = columns(strip, 7, gap=REVIEW_DAY_GAP)
    assert cues == via
    leftover = strip.w - REVIEW_DAY_GAP * 6
    assert cues[0].w == pytest.approx(leftover / 7)
    assert cues[1].x == pytest.approx(cues[0].right + REVIEW_DAY_GAP)

    label, write = review_day_parts(cues[0])
    assert label.y > cues[0].y
    assert write.bottom < cues[0].bottom
    assert write.y > label.bottom
    hits = review_day_link_hits(cues[0])
    assert hits == (label,)
    assert not any(_rects_overlap(hit, write) for hit in hits)


def test_reviews_index_seats():
    well = well_rect(NOMAD)
    seats = reviews_index_rows(well, 14)
    assert len(seats) == 14
    assert seats[0].y == pytest.approx(well.y)
    assert seats[-1].bottom == pytest.approx(well.bottom)
    leftover = well.h - REVIEW_INDEX_GAP * 13
    assert seats[0].h == pytest.approx(leftover / 14)
    stub, dated = reviews_index_week_parts(seats[0])
    assert stub.w == pytest.approx(REVIEW_INDEX_WEEK_W)
    assert dated.x == pytest.approx(stub.right)
    assert reviews_index_link_hits(seats[0]) == (stub, dated)


def test_review_paint_day_cues_and_unlabeled_narrative():
    spec = Spec(notes_pages=1, months=(1, 2, 3))
    page = next(p for p in ReviewSection(spec).pages() if p.dest == "review-2026-W01")
    dest = next(item for item in page.components if isinstance(item, ReviewWeekPage))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_review(plotter, well, dest)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("Review") == 0
    assert texts.count("Notes") == 0
    assert texts.count("Week") == 0
    for label in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"):
        assert label in texts
    assert "29" in texts
    assert "1" in texts
    assert "4" in texts

    strip, notes = review_seats(well)
    cues = review_day_cues(strip)
    boxes = [
        op[1]
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(cues[0].w)
    ]
    assert len(boxes) == 7
    note_box = next(
        op[1] for op in plotter.ops if op[0] == "rect" and op[2] and not op[3] and op[1] == notes
    )
    assert note_box == notes

    links = [(op[1], op[2]) for op in plotter.ops if op[0] == "link"]
    assert [dest_name for _hit, dest_name in links] == [
        "2026-01-01",
        "2026-01-02",
        "2026-01-03",
        "2026-01-04",
    ]
    for cue, day in zip(cues, dest.days, strict=True):
        label, write = review_day_parts(cue)
        if day.dest:
            assert (label, day.dest) in links
            assert not any(_rects_overlap(hit, write) for hit, _dest in links)
        else:
            assert all(op[2] != day.day.isoformat() for op in plotter.ops if op[0] == "link")

    rules = [
        op
        for op in plotter.ops
        if op[0] == "line" and op[5] == pytest.approx(RULE) and op[6] == pytest.approx(RULE_C)
    ]
    for cue in cues:
        _label, write = review_day_parts(cue)
        assert any(
            op[1] == pytest.approx(write.x)
            and op[3] == pytest.approx(write.right)
            and op[2] == pytest.approx(write.bottom)
            for op in rules
        )


def test_reviews_index_paint_week_links():
    spec = Spec(notes_pages=1, months=(1, 2, 3))
    page = next(p for p in ReviewSection(spec).pages() if p.kind == "reviews_index")
    index = next(item for item in page.components if isinstance(item, ReviewIndex))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_reviews_index(plotter, well, index)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    for week in range(1, 15):
        assert f"W{week:02d}" in texts
    assert "29 Dec–4 Jan" in texts
    assert short_date_range(date(2026, 1, 26), date(2026, 2, 1)) in texts
    assert "Review" not in texts
    assert "January" not in texts

    links = [op[2] for op in plotter.ops if op[0] == "link"]
    assert links == [dest for week in range(1, 15) for dest in (f"review-2026-W{week:02d}",) * 2]
    seats = reviews_index_rows(well, len(index.weeks))
    expected: list[tuple[Rect, str]] = []
    for seat, dest_name in zip(seats, [f"review-2026-W{week:02d}" for week in range(1, 15)], strict=True):
        for hit in reviews_index_link_hits(seat):
            expected.append((hit, dest_name))
    assert [(op[1], op[2]) for op in plotter.ops if op[0] == "link"] == expected


def test_review_header_week_chip_and_rev_tab():
    spec = Spec(notes_pages=1, months=(1, 2, 3))
    page = next(p for p in ReviewSection(spec).pages() if p.dest == "review-2026-W01")
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Review" in texts
    assert texts.count("Review") == 1
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
        if isinstance(item, ReviewIndex)
    )
    calendar = month_week_bands(2026, (1, 2, 3), weekday_start=0)
    weeks = [week for _month, band in calendar for week in band]
    assert len(index.weeks) == len(weeks)
    assert index.weeks[0].monday == weeks[0][0]
