from parch.books import YearPlanner
from parch.layouts.planner.painters import strip_active, strip_items
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


def test_extras_chips_365_after_year_fav_100_after_notes():
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
        ("365", spec.checkoff_365_dest),
        ("Quar", "quarter-2026-Q1"),
        ("Mon", "month-2026-01"),
        ("Habit", "month-2026-01-habits"),
        ("Week", "week-2026-W01"),
        ("Rev", "review-index-2026"),
        ("Day", "2026-01-01"),
        ("Notes", "2026-01-01-notes-1"),
        ("Fav", spec.favorites_dest),
        ("100", spec.my_100_dest),
        ("Proj", "projects-index-2026-01"),
        ("Meet", "meetings-index-2026"),
        ("Task", "tasks-index-2026-Q1"),
    )


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
    assert strip_active(fav) == "Fav"
    assert strip_active(hundred) == "100"
    assert strip_active(checkoff) == "365"
