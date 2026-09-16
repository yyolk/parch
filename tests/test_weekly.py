from datetime import date

from inline_snapshot import snapshot

from parch.books import YearPlanner
from parch.calendar import month_touching_weeks, months_touching_weeks
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


def test_q1_weeks_are_unique():
    weeks = months_touching_weeks(2026, (1, 2, 3), weekday_start=0)
    keys = [week[0].isocalendar()[:2] for week in weeks]
    assert len(keys) == len(set(keys))
    assert len(weeks) == 14
    assert weeks[0][0] == date(2025, 12, 29)
    assert weeks[-1][-1] == date(2026, 4, 5)


def test_year_weeks_are_unique():
    weeks = months_touching_weeks(2026, tuple(range(1, 13)), weekday_start=0)
    keys = [week[0].isocalendar()[:2] for week in weeks]
    assert len(keys) == len(set(keys))
    assert len(weeks) == 53
    assert weeks[0][0] == date(2025, 12, 29)
    assert weeks[-1][0] == date(2026, 12, 28)


def test_week_dests_and_nav_strip():
    spec = Spec(notes_pages=1)
    pages = YearPlanner().pages(spec)
    dests = [page.dest for page in pages]
    assert dests[0:4] == snapshot(
        ["cover", "year-2026", "projects-index-2026-01", "projects-2026-01"]
    )
    assert dests[11] == "meetings-index-2026"
    assert dests[139:144] == snapshot(
        [
            "quarter-2026-Q1",
            "quarter-2026-Q2",
            "quarter-2026-Q3",
            "quarter-2026-Q4",
            "month-2026-01",
        ]
    )
    assert dests.index("week-2026-W02") < dests.index("2026-01-05")
    assert dests.index("week-2026-W05") < dests.index("2026-01-26")
    assert dests.index("month-2026-07") < dests.index("week-2026-W01")
    assert [name for name in dests if name.startswith("week-")] == snapshot(
        [
            "week-2026-W01",
            "week-2026-W02",
            "week-2026-W03",
            "week-2026-W04",
            "week-2026-W05",
            "week-2026-W06",
            "week-2026-W07",
            "week-2026-W08",
            "week-2026-W09",
            "week-2026-W10",
            "week-2026-W11",
            "week-2026-W12",
            "week-2026-W13",
            "week-2026-W14",
            "week-2026-W15",
            "week-2026-W16",
            "week-2026-W17",
            "week-2026-W18",
            "week-2026-W19",
            "week-2026-W20",
            "week-2026-W21",
            "week-2026-W22",
            "week-2026-W23",
            "week-2026-W24",
            "week-2026-W25",
            "week-2026-W26",
            "week-2026-W27",
            "week-2026-W28",
            "week-2026-W29",
            "week-2026-W30",
            "week-2026-W31",
            "week-2026-W32",
            "week-2026-W33",
            "week-2026-W34",
            "week-2026-W35",
            "week-2026-W36",
            "week-2026-W37",
            "week-2026-W38",
            "week-2026-W39",
            "week-2026-W40",
            "week-2026-W41",
            "week-2026-W42",
            "week-2026-W43",
            "week-2026-W44",
            "week-2026-W45",
            "week-2026-W46",
            "week-2026-W47",
            "week-2026-W48",
            "week-2026-W49",
            "week-2026-W50",
            "week-2026-W51",
            "week-2026-W52",
            "week-2026-W53",
        ]
    )

    month = next(page for page in pages if page.dest == "month-2026-01")
    assert strip_items(month) == snapshot(
        (
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
    )
    assert strip_active(month.kind) == "Mon"

    feb = next(page for page in pages if page.dest == "month-2026-02")
    assert ("Mon", "month-2026-02") in strip_items(feb)
    assert ("Day", "2026-02-01") in strip_items(feb)
    assert ("Notes", "2026-02-01-notes-1") in strip_items(feb)

    w01 = next(page for page in pages if page.dest == "week-2026-W01")
    assert strip_active(w01.kind) == "Week"
    assert ("Week", "week-2026-W01") in strip_items(w01)
    assert ("Day", "2026-01-01") in strip_items(w01)
    assert ("Habit", "month-2026-01-habits") in strip_items(w01)

    jan15 = next(page for page in pages if page.dest == "2026-01-15")
    assert ("Week", "week-2026-W03") in strip_items(jan15)
    assert strip_active(jan15.kind) == "Day"

    notes = next(page for page in pages if page.dest == "2026-01-15-notes-1")
    assert ("Week", "week-2026-W03") in strip_items(notes)
    assert strip_active(notes.kind) == "Notes"

    w06 = next(page for page in pages if page.dest == "week-2026-W06")
    assert ("Day", "2026-02-02") in strip_items(w06)
    assert ("Notes", "2026-02-02-notes-1") in strip_items(w06)


def test_week_pages_link_pressed_days_only():
    spec = Spec(notes_pages=1)
    plotter = RecordingPlotter()
    YearPlanner().plot(spec, plotter)
    links = plotter.links()
    dests = plotter.dests()
    assert "week-2026-W01" in links
    assert "week-2026-W14" in links
    assert "2026-01-01" in links
    assert "2026-02-01" in dests
    assert "2026-03-31" in dests
    assert "2026-04-01" in dests
    assert "2026-12-31" in dests
    assert "2025-12-29" not in dests
    assert "week-2026-W53" in dests

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Week 01" in texts
    assert "Week" in texts
