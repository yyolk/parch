from datetime import date

from parch.books import YearPlanner
from parch.devices.registry import NOMAD
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.painters import strip_active, strip_items
from parch.plotter import RecordingPlotter
from parch.spec import Spec

_DEFAULT_LABELS = (
    "Year",
    "Quar",
    "Mon",
    "Habit",
    "Week",
    "Rev",
    "Day",
    "Notes",
    "Proj",
    "Meet",
    "Task",
)


def _labels(page) -> list[str]:
    return [label for label, _dest in strip_items(page)]


def test_strip_unchanged_when_extras_off():
    spec = Spec(notes_pages=1, months=(1,))
    year = next(page for page in YearPlanner().pages(spec) if page.kind == "annual")
    assert _labels(year) == list(_DEFAULT_LABELS)
    chips = dict(strip_items(year))
    assert "Fav" not in chips
    assert "100" not in chips
    assert "365" not in chips


def test_extras_chips_after_notes_before_proj():
    spec = Spec(
        notes_pages=1,
        favorites_pages=1,
        my_100=True,
        checkoff_365=True,
        months=(1,),
    )
    year = next(page for page in YearPlanner().pages(spec) if page.kind == "annual")
    assert strip_items(year) == (
        ("Year", "year-2026"),
        ("Quar", "quarter-2026-Q1"),
        ("Mon", "month-2026-01"),
        ("Habit", "month-2026-01-habits"),
        ("Week", "week-2026-W01"),
        ("Rev", "review-index-2026"),
        ("Day", "2026-01-01"),
        ("Notes", "2026-01-01-notes-1"),
        ("Fav", spec.favorites_dest),
        ("100", spec.my_100_dest),
        ("365", spec.checkoff_365_dest),
        ("Proj", "projects-index-2026-01"),
        ("Meet", "meetings-index-2026"),
        ("Task", "tasks-index-2026-Q1"),
    )


def test_extras_chips_without_notes():
    spec = Spec(
        notes_pages=0,
        favorites_pages=1,
        my_100=True,
        checkoff_365=True,
        months=(1,),
    )
    year = next(page for page in YearPlanner().pages(spec) if page.kind == "annual")
    assert _labels(year) == [
        "Year",
        "Quar",
        "Mon",
        "Habit",
        "Week",
        "Rev",
        "Day",
        "Fav",
        "100",
        "365",
        "Proj",
        "Meet",
        "Task",
    ]
    assert "Notes" not in _labels(year)


def test_each_extra_is_independent():
    fav = Spec(notes_pages=1, favorites_pages=1, months=(1,))
    hundred = Spec(notes_pages=1, my_100=True, months=(1,))
    checkoff = Spec(notes_pages=1, checkoff_365=True, months=(1,))
    fav_year = next(page for page in YearPlanner().pages(fav) if page.kind == "annual")
    hundred_year = next(
        page for page in YearPlanner().pages(hundred) if page.kind == "annual"
    )
    checkoff_year = next(
        page for page in YearPlanner().pages(checkoff) if page.kind == "annual"
    )
    assert _labels(fav_year) == [
        "Year",
        "Quar",
        "Mon",
        "Habit",
        "Week",
        "Rev",
        "Day",
        "Notes",
        "Fav",
        "Proj",
        "Meet",
        "Task",
    ]
    assert _labels(hundred_year) == [
        "Year",
        "Quar",
        "Mon",
        "Habit",
        "Week",
        "Rev",
        "Day",
        "Notes",
        "100",
        "Proj",
        "Meet",
        "Task",
    ]
    assert _labels(checkoff_year) == [
        "Year",
        "Quar",
        "Mon",
        "Habit",
        "Week",
        "Rev",
        "Day",
        "Notes",
        "365",
        "Proj",
        "Meet",
        "Task",
    ]


def test_extras_landing_dests_from_every_page_type():
    spec = Spec(
        notes_pages=1,
        favorites_pages=1,
        my_100=True,
        checkoff_365=True,
        months=(1,),
    )
    pages = YearPlanner().pages(spec)
    jan1 = date(2026, 1, 1)
    samples = (
        spec.year_dest,
        spec.dest_for_quarter(1),
        spec.dest_for_month(1),
        spec.dest_for_habits(1),
        spec.dest_for_week(jan1),
        spec.dest_for_day(jan1),
        spec.dest_for_notes(jan1, 1),
        spec.review_index_dest,
        spec.dest_for_review(jan1),
        spec.projects_index_dest,
        spec.dest_for_project(1),
        spec.meetings_index_dest,
        spec.dest_for_meeting(1),
        spec.tasks_index_dest,
        spec.dest_for_task(jan1),
        spec.favorites_dest,
        spec.my_100_dest,
        spec.checkoff_365_dest,
    )
    by_dest = {page.dest: page for page in pages}
    for dest in samples:
        page = by_dest[dest]
        chips = dict(strip_items(page))
        assert chips["Fav"] == spec.favorites_dest
        assert chips["100"] == spec.my_100_dest
        assert chips["365"] == spec.checkoff_365_dest


def test_extras_strip_active_on_own_pages():
    spec = Spec(
        notes_pages=0,
        favorites_pages=1,
        my_100=True,
        checkoff_365=True,
        months=(1,),
    )
    pages = YearPlanner().pages(spec)
    fav = next(page for page in pages if page.kind == "favorites")
    hundred = next(page for page in pages if page.kind == "my_100")
    checkoff = next(page for page in pages if page.kind == "checkoff_365")
    year = next(page for page in pages if page.kind == "annual")
    assert strip_active(fav.kind) == "Fav"
    assert strip_active(hundred.kind) == "100"
    assert strip_active(checkoff.kind) == "365"
    assert strip_active(year.kind) == "Year"


def test_extras_chips_paint_and_link():
    spec = Spec(
        notes_pages=1,
        favorites_pages=1,
        my_100=True,
        checkoff_365=True,
        months=(1,),
    )
    year = next(page for page in YearPlanner().pages(spec) if page.kind == "annual")
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(year, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    links = [op[2] for op in plotter.ops if op[0] == "link"]
    for label in ("Fav", "100", "365"):
        assert label in texts
    assert spec.favorites_dest in links
    assert spec.my_100_dest in links
    assert spec.checkoff_365_dest in links

    off = next(
        page
        for page in YearPlanner().pages(Spec(notes_pages=1, months=(1,)))
        if page.kind == "annual"
    )
    blank = RecordingPlotter()
    blank.begin_page()
    PlannerLayout().paint(off, blank, NOMAD)
    off_texts = [op[2] for op in blank.ops if op[0] == "text"]
    assert "Fav" not in off_texts
    assert "100" not in off_texts
    assert "365" not in off_texts
