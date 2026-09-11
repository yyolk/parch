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
    HAIR,
    REVIEW_DAY_GAP,
    REVIEW_GAP,
    REVIEW_INDEX_BAND_GAP,
    REVIEW_INDEX_CHIP_GAP,
    REVIEW_INDEX_CHIP_H,
    REVIEW_INDEX_CHIP_INSET_X,
    REVIEW_INDEX_LABEL_GAP,
    REVIEW_INDEX_MONTH_W,
    REVIEW_STRIP_H,
    RULE,
    RULE_C,
    SOFT,
    paint_review,
    paint_review_index,
    review_day_cues,
    review_day_link_hits,
    review_day_parts,
    review_day_rule_y,
    review_index_chip,
    review_index_cols,
    review_index_link_hits,
    review_index_month_rows,
    review_index_row_parts,
    review_index_rule_y,
    review_seats,
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
    ("Task", "tasks-index-2026-Q1"),
    ("Rev", "review-index-2026"),
    ("Week", "week-2026-W01"),
    ("Day", "2026-01-01"),
    ("Notes", "2026-01-01-notes-1"),
)


def test_review_in_year_planner_after_tasks():
    spec = Spec(notes_pages=1)
    pages = YearPlanner().pages(spec)
    dests = [page.dest for page in pages]
    kinds = [page.kind for page in pages]
    assert dests[28] == "tasks-index-2026-Q1"
    assert dests[85] == "review-index-2026"
    assert dests[86] == "review-2026-W01"
    assert dests[138] == "review-2026-W53"
    assert dests[139] == "quarter-2026-Q1"
    assert kinds.count("review_index") == 1
    assert kinds.count("review") == 53
    year = next(page for page in pages if page.kind == "annual")
    labels = [label for label, _ in strip_items(year)]
    assert labels == ["Year", "Quar", "Mon", "Habit", "Proj", "Meet", "Task", "Rev", "Week", "Day", "Notes"]
    assert dict(strip_items(year))["Rev"] == spec.review_index_dest


def test_review_index_page():
    spec = Spec(notes_pages=1)
    page = next(p for p in ReviewSection(spec).pages() if p.kind == "review_index")
    assert page.dest == "review-index-2026"
    assert page.title == "Review"
    index = next(item for item in page.components if isinstance(item, ReviewIndex))
    assert index.year == 2026
    assert index.dest == "review-index-2026"
    assert [band.month for band in index.bands] == list(range(1, 13))
    assert [band.name for band in index.bands] == [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]
    assert [len(band.weeks) for band in index.bands] == [5, 4, 5, 4, 4, 5, 4, 5, 4, 4, 5, 4]
    assert index.bands[0].weeks[0].dest == "review-2026-W01"
    assert index.bands[0].weeks[-1].iso_week == 5
    assert index.bands[1].weeks[0].iso_week == 6
    assert index.bands[-1].weeks[-1].iso_week == 53
    assert strip_active(page.kind) == "Rev"
    assert strip_items(page) == _REV_STRIP


def test_review_dest_page():
    spec = Spec(notes_pages=1)
    page = next(p for p in ReviewSection(spec).pages() if p.dest == "review-2026-W01")
    assert page.kind == "review"
    assert page.title == "Review"
    dest = next(item for item in page.components if isinstance(item, ReviewWeekPage))
    assert dest.year == 2026
    assert dest.iso_year == 2026
    assert dest.iso_week == 1
    assert dest.monday == date(2025, 12, 29)
    assert dest.sunday == date(2026, 1, 4)
    assert dest.index_dest == "review-index-2026"
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
    assert ("Rev", "review-index-2026") in strip_items(page)
    assert ("Week", "week-2026-W01") in strip_items(page)


def test_review_section_order_index_then_weeks():
    spec = Spec(notes_pages=1)
    dests = [page.dest for page in ReviewSection(spec).pages()]
    assert dests[0] == "review-index-2026"
    assert dests[1:] == [f"review-2026-W{week:02d}" for week in range(1, 54)]
    assert dests.count("review-index-2026") == 1
    assert [page.kind for page in ReviewSection(spec).pages()].count("review_index") == 1
    assert [page.kind for page in ReviewSection(spec).pages()].count("review") == 53
    week_dests = [dest for dest in dests if dest.startswith("review-2026-W")]
    assert week_dests == [f"review-2026-W{week:02d}" for week in range(1, 54)]
    assert len(week_dests) == len(set(week_dests))
    july = next(p for p in ReviewSection(spec).pages() if p.dest == "review-2026-W29")
    well = next(item for item in july.components if isinstance(item, ReviewWeekPage))
    assert well.index_dest == "review-index-2026"
    assert dict(strip_items(july))["Rev"] == "review-index-2026"
    assert dict(strip_items(july))["Quar"] == "quarter-2026-Q3"


def test_review_index_seats_equal_month_rows_and_chip_columns():
    well = well_rect(NOMAD)
    counts = (5, 4, 5)
    n_cols = review_index_cols(counts)
    assert n_cols == 5
    bands = review_index_month_rows(well, 3)
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
    via_rows = rows(well, 3, gap=REVIEW_INDEX_BAND_GAP)
    assert bands == via_rows

    stub, chips = review_index_row_parts(bands[0], 5, n_cols)
    assert stub.w == pytest.approx(REVIEW_INDEX_MONTH_W)
    assert stub.x == pytest.approx(bands[0].x)
    assert len(chips) == 5
    assert chips[0].x > stub.right
    assert chips[-1].right == pytest.approx(bands[0].right)
    grid_w = max(bands[0].w - REVIEW_INDEX_MONTH_W - REVIEW_INDEX_LABEL_GAP, 1)
    via_cols = columns(
        bands[0], 2, gap=REVIEW_INDEX_LABEL_GAP, weights=(REVIEW_INDEX_MONTH_W, grid_w)
    )
    assert stub == via_cols[0]
    assert chips == columns(via_cols[1], n_cols, gap=REVIEW_INDEX_CHIP_GAP)

    feb_stub, feb_chips = review_index_row_parts(bands[1], 4, n_cols)
    assert len(feb_chips) == 4
    assert feb_chips[0].w == pytest.approx(chips[0].w)
    assert feb_chips[0].x == pytest.approx(chips[0].x)
    assert feb_chips[1].x == pytest.approx(chips[1].x)
    assert feb_stub.w == pytest.approx(stub.w)

    chip = review_index_chip(chips[0])
    assert chip.h == pytest.approx(REVIEW_INDEX_CHIP_H)
    assert chip.x == pytest.approx(chips[0].x + REVIEW_INDEX_CHIP_INSET_X)
    assert chip.w == pytest.approx(chips[0].w - 2 * REVIEW_INDEX_CHIP_INSET_X)
    assert chip.y == pytest.approx(chips[0].y + (chips[0].h - REVIEW_INDEX_CHIP_H) / 2)
    assert chip.bottom < chips[0].bottom
    assert chip.y > chips[0].y
    assert review_index_link_hits(chips[0]) == (chip,)
    assert review_index_rule_y(bands[0]) == pytest.approx(bands[0].bottom)


def test_review_index_paint_month_headers_hairlines_and_week_links():
    spec = Spec(notes_pages=1)
    page = next(p for p in ReviewSection(spec).pages() if p.kind == "review_index")
    index = next(item for item in page.components if isinstance(item, ReviewIndex))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_review_index(plotter, well, index)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    january = next(op for op in plotter.ops if op[0] == "text" and op[2] == "January")
    assert january[7] == "bold"
    week = next(op for op in plotter.ops if op[0] == "text" and op[2] == "W01")
    assert week[7] == "medium"
    assert week[8] == "jost"
    for name in (
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ):
        assert name in texts
    for week in range(1, 54):
        assert f"W{week:02d}" in texts
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
        "Notes",
        "P",
    ):
        assert rejected not in texts

    links = [op[2] for op in plotter.ops if op[0] == "link"]
    assert links == [f"review-2026-W{week:02d}" for week in range(1, 54)]
    counts = tuple(len(band.weeks) for band in index.bands)
    n_cols = review_index_cols(counts)
    seats = [
        cell
        for band_box, band in zip(
            review_index_month_rows(well, len(index.bands)), index.bands, strict=True
        )
        for cell in review_index_row_parts(band_box, len(band.weeks), n_cols)[1]
    ]
    expected_hits: list[tuple[Rect, str]] = []
    for seat, dest in zip(
        seats, [f"review-2026-W{week:02d}" for week in range(1, 54)], strict=True
    ):
        hits = review_index_link_hits(seat)
        assert hits == (review_index_chip(seat),)
        expected_hits.extend((hit, dest) for hit in hits)
    assert [(op[1], op[2]) for op in plotter.ops if op[0] == "link"] == expected_hits
    for seat in seats:
        assert all(op[1] != seat for op in plotter.ops if op[0] == "link")

    hairlines = [
        op
        for op in plotter.ops
        if op[0] == "line"
        and op[5] == pytest.approx(HAIR)
        and op[6] == pytest.approx(SOFT)
    ]
    assert len(hairlines) == 11
    month_rows = review_index_month_rows(well, 12)
    for row, line in zip(month_rows[:-1], hairlines, strict=True):
        assert line[1] == pytest.approx(well.x)
        assert line[3] == pytest.approx(well.right)
        rule_y = review_index_rule_y(row)
        assert line[2] == pytest.approx(rule_y)
        assert line[4] == pytest.approx(rule_y)
        assert rule_y == pytest.approx(row.bottom)

    chips = [
        op[1]
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3]
    ]
    assert len(chips) == 53
    for seat, box in zip(seats, chips, strict=True):
        assert box == review_index_chip(seat)


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
    assert write.y == pytest.approx(label.bottom)
    hits = review_day_link_hits(cues[0])
    assert hits == (label,)
    assert not any(_rects_overlap(hit, write) for hit in hits)
    rule_y = review_day_rule_y(cues[0])
    assert rule_y > write.y
    assert rule_y < write.bottom
    assert rule_y < cues[0].bottom


def test_review_paint_day_cues_and_unlabeled_narrative():
    spec = Spec(notes_pages=1)
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
        rule_y = review_day_rule_y(cue)
        assert any(
            op[1] == pytest.approx(write.x)
            and op[3] == pytest.approx(write.right)
            and op[2] == pytest.approx(rule_y)
            for op in rules
        )


def test_review_header_week_chip_and_rev_tab():
    spec = Spec(notes_pages=1)
    page = next(p for p in ReviewSection(spec).pages() if p.dest == "review-2026-W01")
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Review" in texts
    assert texts.count("Review") == 1
    assert "W01" in texts
    assert "2026" in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Proj", "Meet", "Task", "Rev", "Week", "Day", "Notes"):
        assert label in texts
    assert strip_active(page.kind) == "Rev"
    links = [op[2] for op in plotter.ops if op[0] == "link"]
    assert links.count("review-index-2026") >= 2
    chip = next(op[1] for op in plotter.ops if op[0] == "text" and op[2] == "W01")
    assert any(
        op[0] == "link" and op[2] == "review-index-2026" and _rects_overlap(op[1], chip)
        for op in plotter.ops
    )


def test_review_index_chrome_rev_tab():
    spec = Spec(notes_pages=1)
    page = next(p for p in ReviewSection(spec).pages() if p.kind == "review_index")
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Review" in texts
    assert "2026" in texts
    assert "January" in texts
    assert "Rev" in texts
    assert strip_active(page.kind) == "Rev"
    assert dict(strip_items(page))["Rev"] == spec.review_index_dest


def test_review_q1_subset_one_index():
    spec = Spec(notes_pages=1, months=(1, 2, 3))
    pages = ReviewSection(spec).pages()
    index = next(p for p in pages if p.kind == "review_index")
    roster = next(item for item in index.components if isinstance(item, ReviewIndex))
    assert [band.month for band in roster.bands] == [1, 2, 3]
    dests = [page.dest for page in pages]
    assert dests[0] == "review-index-2026"
    assert dests[1:] == [f"review-2026-W{week:02d}" for week in range(1, 15)]
    dest = next(item for item in pages[1].components if isinstance(item, ReviewWeekPage))
    assert dest.index_dest == "review-index-2026"


def test_q1_bands_match_calendar():
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
