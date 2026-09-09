from parch.books import YearPlanner
from parch.components import QuarterGrid
from parch.layouts.planner.painters import strip_active, strip_items
from parch.plotter import RecordingPlotter
from parch.spec import Spec


def test_quarter_page_and_provisional_nav():
    spec = Spec(notes_pages=1)
    pages = YearPlanner().pages(spec)
    assert [page.dest for page in pages[:7]] == [
        "cover",
        "year-2026",
        "quarter-2026-Q1",
        "month-2026-01",
        "month-2026-02",
        "month-2026-03",
        "week-2026-W01",
    ]
    assert [page.dest for page in pages if page.dest.startswith("quarter-")] == [
        "quarter-2026-Q1"
    ]

    quarter = pages[2]
    assert quarter.kind == "quarter"
    assert quarter.title == "Q1 2026"
    assert strip_active(quarter.kind) == "Quar"
    assert strip_items(quarter) == (
        ("Year", "year-2026"),
        ("Quar", "quarter-2026-Q1"),
        ("Mon", "month-2026-01"),
        ("Week", "week-2026-W01"),
        ("Day", "2026-01-01"),
        ("Notes", "2026-01-01-notes-1"),
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


def test_quarter_links_from_year_and_month_meta():
    plotter = RecordingPlotter()
    YearPlanner().plot(Spec(notes_pages=1), plotter)
    assert "quarter-2026-Q1" in plotter.dests()
    assert "quarter-2026-Q1" in plotter.links()
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Q1 2026" in texts
    assert "Quar" in texts
