import pytest

from parch.books import YearPlanner
from parch.components import QuarterGrid
from parch.geom import Rect
from parch.layouts.planner.painters import (
    FOCUS_ROWS,
    focus_content_height,
    paint_quarter,
    quarter_seats,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.spec import Spec
from parch.tracks import rows


def test_quarter_page_and_nav():
    spec = Spec(notes_pages=1)
    pages = YearPlanner().pages(spec)
    assert [page.dest for page in pages[:4]] == [
        "cover",
        "year-2026",
        "projects-index-2026-01",
        "projects-2026-01",
    ]
    assert [page.dest for page in pages[11:12]] == ["meetings-index-2026"]
    assert [page.dest for page in pages[139:144]] == [
        "quarter-2026-Q1",
        "quarter-2026-Q2",
        "quarter-2026-Q3",
        "quarter-2026-Q4",
        "month-2026-01",
    ]
    assert [page.dest for page in pages if page.dest.startswith("quarter-")] == [
        "quarter-2026-Q1",
        "quarter-2026-Q2",
        "quarter-2026-Q3",
        "quarter-2026-Q4",
    ]

    quarter = next(page for page in pages if page.dest == "quarter-2026-Q1")
    assert quarter.kind == "quarter"
    assert quarter.title == "Q1 2026"
    assert strip_active(quarter.kind) == "Quar"
    assert strip_items(quarter) == (
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

    grid = next(item for item in quarter.components if isinstance(item, QuarterGrid))
    assert grid.quarter == 1
    assert [month.name[:3] for month in grid.months] == ["Jan", "Feb", "Mar"]
    assert grid.months[0].dest == "month-2026-01"
    assert any(cell.dest == "2026-01-15" for week in grid.months[0].weeks for cell in week)

    annual = pages[1]
    assert ("Quar", "quarter-2026-Q1") in strip_items(annual)
    feb = next(page for page in pages if page.dest == "month-2026-02")
    assert ("Quar", "quarter-2026-Q1") in strip_items(feb)
    jan15 = next(page for page in pages if page.dest == "2026-01-15")
    assert ("Quar", "quarter-2026-Q1") in strip_items(jan15)
    july = next(page for page in pages if page.dest == "month-2026-07")
    assert ("Quar", "quarter-2026-Q3") in strip_items(july)
    q3 = next(page for page in pages if page.dest == "quarter-2026-Q3")
    assert q3.title == "Q3 2026"


def test_quarter_links_from_year_and_month_meta():
    plotter = RecordingPlotter()
    YearPlanner().plot(Spec(notes_pages=1), plotter)
    assert "quarter-2026-Q1" in plotter.dests()
    assert "quarter-2026-Q3" in plotter.dests()
    assert "quarter-2026-Q1" in plotter.links()
    assert "quarter-2026-Q3" in plotter.links()
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Q1 2026" in texts
    assert "Q3 2026" in texts
    assert "Quar" in texts
    assert "Focus" in texts
    assert "Notes" in texts


def test_quarter_seats_focus_over_notes():
    box = Rect(4, 20, 110, 90)
    months, focus, notes = quarter_seats(box)
    jan, feb, mar = months
    year_band = rows(box, 4, gap=2.6)[0].h
    assert jan.h == pytest.approx(year_band)
    assert jan.y == feb.y == mar.y == pytest.approx(box.y)
    assert jan.x == pytest.approx(box.x)
    assert mar.right == pytest.approx(box.right)
    assert focus.x == pytest.approx(notes.x)
    assert focus.x == pytest.approx(box.x)
    assert focus.w == pytest.approx(notes.w)
    assert focus.w == pytest.approx(box.w)
    assert focus.y > jan.bottom
    assert notes.y == pytest.approx(focus.bottom + 2.6)
    assert notes.bottom == pytest.approx(box.bottom)
    assert focus.h == pytest.approx(focus_content_height())


def test_quarter_paint():
    spec = Spec(notes_pages=1)
    grid = next(
        item
        for item in next(
            page for page in YearPlanner().pages(spec) if page.dest == "quarter-2026-Q1"
        ).components
        if isinstance(item, QuarterGrid)
    )
    well = Rect(4, 20, 110, 120)
    plotter = RecordingPlotter()
    paint_quarter(plotter, well, grid)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Jan" in texts and "Feb" in texts and "Mar" in texts
    assert "Focus" in texts
    assert "Notes" in texts
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(2.4)
    ]
    assert len(ticks) == FOCUS_ROWS
