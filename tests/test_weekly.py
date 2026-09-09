from datetime import date

from parch.books import YearPlanner
from parch.calendar import month_touching_weeks
from parch.layouts.planner.painters import strip_active, strip_items
from parch.plotter import RecordingPlotter
from parch.spec import Spec


def test_january_2026_touching_weeks():
    weeks = month_touching_weeks(2026, 1, weekday_start=0)
    assert len(weeks) == 5
    assert weeks[0][0] == date(2025, 12, 29)
    assert weeks[0][3] == date(2026, 1, 1)
    assert weeks[1][0] == date(2026, 1, 5)
    assert weeks[-1][-1] == date(2026, 2, 1)


def test_week_dests_and_nav_strip():
    spec = Spec(notes_pages=1)
    pages = YearPlanner().pages(spec)
    dests = [page.dest for page in pages]
    assert dests[0:4] == ["cover", "year-2026", "month-2026-01", "week-2026-W01"]
    assert dests.index("week-2026-W02") < dests.index("2026-01-05")
    assert dests.index("week-2026-W05") < dests.index("2026-01-26")
    assert [name for name in dests if name.startswith("week-")] == [
        "week-2026-W01",
        "week-2026-W02",
        "week-2026-W03",
        "week-2026-W04",
        "week-2026-W05",
    ]

    month = next(page for page in pages if page.dest == "month-2026-01")
    assert strip_items(month) == (
        ("Year", "year-2026"),
        ("Mon", "month-2026-01"),
        ("Week", "week-2026-W01"),
        ("Day", "2026-01-05"),
        ("Notes", "2026-01-05-notes-1"),
    )
    assert strip_active(month.kind) == "Mon"

    w01 = next(page for page in pages if page.dest == "week-2026-W01")
    assert strip_active(w01.kind) == "Week"
    assert strip_items(w01)[2] == ("Week", "week-2026-W01")
    assert strip_items(w01)[3] == ("Day", "2026-01-01")

    jan15 = next(page for page in pages if page.dest == "2026-01-15")
    assert ("Week", "week-2026-W03") in strip_items(jan15)
    assert strip_active(jan15.kind) == "Day"

    notes = next(page for page in pages if page.dest == "2026-01-15-notes-1")
    assert ("Week", "week-2026-W03") in strip_items(notes)
    assert strip_active(notes.kind) == "Notes"


def test_week_pages_link_in_month_days_only():
    spec = Spec(notes_pages=1)
    plotter = RecordingPlotter()
    YearPlanner().plot(spec, plotter)
    links = plotter.links()
    assert "week-2026-W01" in links
    assert "week-2026-W05" in links
    assert "2026-01-01" in links
    assert "2025-12-29" not in plotter.dests()
    assert "2026-02-01" not in plotter.dests()

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Week 01" in texts
    assert "Week" in texts
