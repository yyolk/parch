from pathlib import Path

import pytest
from pypdf import PdfReader

from parch import ConfigError
from parch.books import YearPlanner, outline_entries
from parch.components import Notes
from parch.layouts.planner.painters import strip_active, strip_items
from parch.press import press
from parch.sections import Days365Section, FavoritesSection, My100Section
from parch.spec import Spec

_STRIP = (
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


def _lists_on(**kwargs: object) -> Spec:
    return Spec(
        months=(1,),
        notes_pages=1,
        lists_favorites=True,
        lists_my_100=True,
        lists_days_365=True,
        **kwargs,
    )


def test_lists_default_off():
    spec = Spec()
    assert spec.lists_favorites is False
    assert spec.lists_my_100 is False
    assert spec.lists_days_365 is False
    assert spec.favorites_dest == "favorites-2026"
    assert spec.my_100_dest == "my-100-2026"
    assert spec.days_365_dest == "days-365-2026"
    assert FavoritesSection(spec).pages() == []
    assert My100Section(spec).pages() == []
    assert Days365Section(spec).pages() == []


def test_lists_toml_closed_table():
    enabled = Spec.from_mapping(
        {"lists": {"favorites": True, "my_100": True, "days_365": True}}
    )
    assert enabled.lists_favorites is True
    assert enabled.lists_my_100 is True
    assert enabled.lists_days_365 is True
    assert Spec.from_mapping({"lists": {"favorites": True}}).lists_my_100 is False
    example = Spec.from_path(Path("examples/nomad-lists.toml"))
    assert example.book == "year-planner"
    assert example.device == "supernote-nomad"
    assert example.lists_favorites is True
    assert example.lists_my_100 is True
    assert example.lists_days_365 is True
    assert example.notes_pages == 1
    assert example.project_index_pages == 3
    assert example.outline is True
    nomad = Spec.from_path(Path("examples/nomad.toml"))
    assert nomad.lists_favorites is False
    with pytest.raises(ConfigError, match="unknown lists key 'index'"):
        Spec.from_mapping({"lists": {"index": True}})
    with pytest.raises(ConfigError, match="lists must be a TOML table"):
        Spec.from_mapping({"lists": True})
    with pytest.raises(ConfigError, match="lists.favorites must be a boolean"):
        Spec.from_mapping({"lists": {"favorites": 1}})


def test_year_planner_inserts_after_calendar_before_review():
    dests = [page.dest for page in YearPlanner().pages(_lists_on())]
    assert dests.index("2026-01-31-notes-1") < dests.index("favorites-2026")
    assert dests.index("favorites-2026") < dests.index("my-100-2026")
    assert dests.index("my-100-2026") < dests.index("days-365-2026")
    assert dests.index("days-365-2026") < dests.index("review-index-2026")
    off = [page.dest for page in YearPlanner().pages(Spec(months=(1,), notes_pages=1))]
    assert "favorites-2026" not in off
    assert off.index("review-index-2026") == dests.index("review-index-2026") - 3


def test_list_stubs_keep_locked_strip():
    pages = YearPlanner().pages(_lists_on())
    favorites = next(page for page in pages if page.kind == "favorites")
    hundred = next(page for page in pages if page.kind == "my_100")
    checkoff = next(page for page in pages if page.kind == "days_365")
    assert favorites.title == "Favorites"
    assert hundred.title == "My 100"
    assert checkoff.title == "365 Days"
    for page in (favorites, hundred, checkoff):
        assert strip_items(page) == _STRIP
        assert strip_active(page.kind) == ""
        assert isinstance(page.components[0], Notes)
        assert page.components[0].label == "placeholder"


def test_lists_outline_and_press(tmp_path: Path):
    spec = _lists_on(outline=True)
    pages = YearPlanner().pages(spec)
    dests = [dest for _title, dest in outline_entries(pages)]
    assert dests[:4] == [
        spec.year_dest,
        spec.quarter_dest,
        spec.month_dest,
        spec.favorites_dest,
    ]
    assert spec.my_100_dest in dests
    assert spec.days_365_dest in dests
    out = tmp_path / "lists.pdf"
    press(spec, out)
    named = {str(key).lstrip("/") for key in (PdfReader(out).named_destinations or {})}
    assert spec.favorites_dest in named
    assert spec.my_100_dest in named
    assert spec.days_365_dest in named
    assert len(PdfReader(out).pages) == len(pages)
