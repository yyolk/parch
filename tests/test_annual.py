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
        "month-2026-01",
        "week-2026-W01",
    ]
    cover = pages[0]
    assert cover.components[0].cta_dest == "year-2026"

    annual = pages[1]
    assert annual.kind == "annual"
    assert strip_active(annual.kind) == "Year"
    assert strip_items(annual) == (
        ("Year", "year-2026"),
        ("Mon", "month-2026-01"),
        ("Week", "week-2026-W01"),
        ("Day", "2026-01-05"),
        ("Notes", "2026-01-05-notes-1"),
    )
    assert all(label != "Cover" for label, _ in strip_items(annual))

    month = pages[2]
    assert strip_items(month)[0] == ("Year", "year-2026")
    assert strip_active(month.kind) == "Mon"

    grid = next(item for item in annual.components if isinstance(item, AnnualGrid))
    january, february = grid.months[0], grid.months[1]
    assert january.dest == "month-2026-01"
    assert february.dest is None
    assert any(cell.dest == "2026-01-15" for week in january.weeks for cell in week)
    assert all(cell.dest is None for week in february.weeks for cell in week)


def test_annual_paint_links_january_only():
    plotter = RecordingPlotter()
    YearPlanner().plot(Spec(notes_pages=1), plotter)
    dests = plotter.dests()
    links = plotter.links()
    assert dests[1] == "year-2026"
    assert "year-2026" in links
    assert "month-2026-01" in links
    assert "2026-01-01" in links
    assert "month-2026-02" not in dests
    assert "month-2026-02" not in links
    assert "2026-02-01" not in dests
    assert "2026-02-01" not in links
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Year" in texts
    assert "Cover" not in texts
    assert "Jan" in texts
    assert "Dec" in texts
