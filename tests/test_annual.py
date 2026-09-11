from parch.books import YearPlanner
from parch.components import AnnualGrid
from parch.layouts.planner.painters import strip_active, strip_items
from parch.plotter import RecordingPlotter
from parch.spec import Spec


def test_annual_page_and_year_nav():
    spec = Spec(notes_pages=1)
    pages = YearPlanner().pages(spec)
    assert [page.dest for page in pages[:4]] == [
        "cover",
        "year-2026",
        "projects-index-2026-01",
        "projects-2026-01",
    ]
    assert [page.dest for page in pages[3:11]] == [
        f"projects-2026-{slot:02d}" for slot in range(1, 9)
    ]
    assert [page.dest for page in pages[11:12]] == ["meetings-index-2026"]
    assert [page.dest for page in pages[139:144]] == [
        "quarter-2026-Q1",
        "quarter-2026-Q2",
        "quarter-2026-Q3",
        "quarter-2026-Q4",
        "month-2026-01",
    ]
    cover = pages[0]
    assert cover.components[0].cta_dest == "year-2026"

    annual = pages[1]
    assert annual.kind == "annual"
    assert strip_active(annual.kind) == "Year"
    assert strip_items(annual) == (
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
    assert all(label != "Cover" for label, _ in strip_items(annual))

    month = next(page for page in pages if page.dest == "month-2026-01")
    assert strip_items(month)[0] == ("Year", "year-2026")
    assert strip_active(month.kind) == "Mon"

    grid = next(item for item in annual.components if isinstance(item, AnnualGrid))
    january, february, march, april = grid.months[:4]
    assert january.dest == "month-2026-01"
    assert february.dest == "month-2026-02"
    assert march.dest == "month-2026-03"
    assert april.dest == "month-2026-04"
    assert grid.months[11].dest == "month-2026-12"
    assert any(cell.dest == "2026-01-15" for week in january.weeks for cell in week)
    assert any(cell.dest == "2026-02-01" for week in february.weeks for cell in week)
    assert any(cell.dest == "2026-04-01" for week in april.weeks for cell in week)


def test_annual_paint_links_all_months():
    plotter = RecordingPlotter()
    YearPlanner().plot(Spec(notes_pages=1), plotter)
    dests = plotter.dests()
    links = plotter.links()
    assert dests[1] == "year-2026"
    assert dests[2] == "projects-index-2026-01"
    assert dests[3:11] == [f"projects-2026-{slot:02d}" for slot in range(1, 9)]
    assert dests[11] == "meetings-index-2026"
    assert dests[139:143] == [
        "quarter-2026-Q1",
        "quarter-2026-Q2",
        "quarter-2026-Q3",
        "quarter-2026-Q4",
    ]
    assert "year-2026" in links
    assert "quarter-2026-Q1" in links
    assert "quarter-2026-Q3" in links
    assert "month-2026-01" in links
    assert "month-2026-07" in links
    assert "month-2026-12" in links
    assert "2026-01-01" in links
    assert "2026-04-01" in dests
    assert "2026-04-01" in links
    assert "2026-07-15" in dests
    assert "2026-12-31" in dests
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Year" in texts
    assert "Cover" not in texts
    assert "Jan" in texts
    assert "Dec" in texts
    assert "Focus" in texts
