from datetime import date
from pathlib import Path

import pytest
from pypdf import PdfReader

from parch import ConfigError
from parch.books import (
    BulletJournal,
    EngineeringNotebook,
    ProjectsNotebook,
    YearPlanner,
    book_for,
    outline_entries,
)
from parch.components import (
    BujoIndex,
    BujoKey,
    CollectionLeaf,
    CoverTitle,
    FutureLogPage,
    HabitGrid,
    MonthlyCalendarList,
    MonthlyTaskWell,
    RapidLogPage,
)
from parch.layouts.planner.painters import (
    BUJO_GUTTER_MM,
    BUJO_ROW_MM,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.spec import Spec

_JAN = Spec(
    book="bullet-journal",
    months=(1,),
    habit_columns=8,
    bujo_index_pages=1,
    bujo_collections=2,
    outline=True,
    title="Bullet journal",
)

_STRIP = ("Key", "Idx", "Fut", "Mon", "Habit", "Day", "Col")


def _named_dests(reader: PdfReader) -> set[str]:
    raw = reader.named_destinations or {}
    return {str(key).lstrip("/") for key in raw}


def test_sealed_component_fields():
    assert set(RapidLogPage.__dataclass_fields__) == {"year", "days"}
    assert "quarter_dest" not in MonthlyCalendarList.__dataclass_fields__
    assert "pattern" not in CollectionLeaf.__dataclass_fields__
    assert "gutter_mm" not in RapidLogPage.__dataclass_fields__
    assert BUJO_GUTTER_MM == 8.0
    assert BUJO_ROW_MM == 5.0


def test_bullet_journal_is_cover_then_bujo_hubs():
    pages = BulletJournal().pages(_JAN)
    kinds = [page.kind for page in pages]
    assert kinds[:5] == ["cover", "bujo_key", "bujo_index", "future_log", "monthly_log"]
    assert kinds[5:8] == ["monthly_tasks", "habits", "rapid_log"]
    assert kinds[-2:] == ["collection", "collection"]
    assert kinds.count("rapid_log") == 31
    assert kinds.count("monthly_log") == 1
    assert kinds.count("habits") == 1
    assert len(pages) == 1 + 1 + 1 + 1 + 1 + 1 + 1 + 31 + 2

    cover = pages[0].components[0]
    assert isinstance(cover, CoverTitle)
    assert cover.cta_dest == _JAN.bujo_key_dest
    assert cover.eyebrow == "Bullet journal"
    assert cover.specs_lead == ""
    assert cover.subtitle == "Bullet journal"

    dests = {page.dest for page in pages}
    assert _JAN.year_dest not in dests
    assert _JAN.quarter_dest not in dests
    assert _JAN.projects_index_dest not in dests
    assert _JAN.bujo_key_dest in dests
    assert _JAN.bujo_index_dest in dests
    assert _JAN.bujo_future_dest in dests
    assert _JAN.dest_for_month(1) in dests
    assert _JAN.dest_for_month_tasks(1) in dests
    assert _JAN.dest_for_habits(1) in dests
    assert _JAN.dest_for_day(date(2026, 1, 1)) in dests
    assert _JAN.dest_for_day(date(2026, 1, 31)) in dests
    assert _JAN.dest_for_bujo_collection(1) in dests
    assert _JAN.dest_for_bujo_collection(2) in dests


def test_january_nav_is_seven_short_chips():
    pages = BulletJournal().pages(_JAN)
    key = next(page for page in pages if page.kind == "bujo_key")
    labels = [label for label, _dest in strip_items(key)]
    assert labels == list(_STRIP)
    assert all(len(label) <= 5 for label in labels)
    assert "Year" not in labels
    assert "Quar" not in labels
    for page in pages[1:]:
        chips = [label for label, _dest in strip_items(page)]
        assert chips == list(_STRIP)
        assert {item.label for item in page.nav} == set(_STRIP)


def test_january_components_and_strip_active():
    pages = BulletJournal().pages(_JAN)
    by_kind = {page.kind: page for page in pages}
    assert isinstance(by_kind["bujo_key"].components[0], BujoKey)
    assert isinstance(by_kind["bujo_index"].components[0], BujoIndex)
    assert isinstance(by_kind["future_log"].components[0], FutureLogPage)
    cal = by_kind["monthly_log"].components[0]
    assert isinstance(cal, MonthlyCalendarList)
    assert not hasattr(cal, "quarter_dest")
    assert cal.tasks_dest == _JAN.dest_for_month_tasks(1)
    assert cal.days[0].dest == "2026-01-01"
    assert isinstance(by_kind["monthly_tasks"].components[0], MonthlyTaskWell)
    grid = by_kind["habits"].components[0]
    assert isinstance(grid, HabitGrid)
    assert grid.rows == 8
    assert grid.quarter_dest is None
    rapid = next(page for page in pages if page.kind == "rapid_log")
    assert isinstance(rapid.components[0], RapidLogPage)
    assert rapid.components[0].days[0].moment == date(2026, 1, 1)
    assert isinstance(by_kind["collection"].components[0], CollectionLeaf)

    assert strip_active("bujo_key") == "Key"
    assert strip_active("bujo_index") == "Idx"
    assert strip_active("future_log") == "Fut"
    assert strip_active("monthly_log") == "Mon"
    assert strip_active("monthly_tasks") == "Mon"
    assert strip_active("habits") == "Habit"
    assert strip_active("rapid_log") == "Day"
    assert strip_active("collection") == "Col"


def test_january_future_log_is_one_band():
    pages = BulletJournal().pages(_JAN)
    future = next(page for page in pages if page.kind == "future_log")
    band = future.components[0]
    assert isinstance(band, FutureLogPage)
    assert band.pages == 1
    assert [month.month for month in band.months] == [1]
    assert band.months[0].dest == _JAN.dest_for_month(1)


def test_january_outline_run_and_each():
    book = BulletJournal()
    pages = book.pages(_JAN)
    plotter = RecordingPlotter()
    book.plot(_JAN, plotter)
    dests = [dest for _title, dest in plotter.outlines()]
    dest_kind = {page.dest: page.kind for page in pages}
    assert dests == [
        _JAN.bujo_key_dest,
        _JAN.bujo_index_dest,
        _JAN.bujo_future_dest,
        _JAN.dest_for_month(1),
        _JAN.dest_for_bujo_collection(1),
    ]
    assert plotter.outlines() == outline_entries(pages)
    assert [dest_kind[dest] for dest in dests] == [
        "bujo_key",
        "bujo_index",
        "future_log",
        "monthly_log",
        "collection",
    ]
    assert _JAN.cover_dest not in dests
    assert _JAN.dest_for_month_tasks(1) not in dests
    assert _JAN.dest_for_habits(1) not in dests
    assert _JAN.dest_for_day(date(2026, 1, 15)) not in dests
    assert _JAN.dest_for_bujo_collection(2) not in dests
    titles = [title for title, _dest in plotter.outlines()]
    assert titles == ["Key", "Index", "Future log", "January 2026", "Collections"]


def test_january_pressable_pdf(tmp_path: Path):
    out = tmp_path / "nomad-bujo-jan.pdf"
    press(_JAN, out)
    reader = PdfReader(out)
    assert len(reader.pages) == 40
    dests = _named_dests(reader)
    assert "cover" in dests
    assert "bujo-key-2026" in dests
    assert "bujo-index-2026-01" in dests
    assert "bujo-future-2026-01" in dests
    assert "month-2026-01" in dests
    assert "month-2026-01-tasks" in dests
    assert "month-2026-01-habits" in dests
    assert "2026-01-01" in dests
    assert "2026-01-31" in dests
    assert "bujo-col-2026-01" in dests
    assert "bujo-col-2026-02" in dests
    assert "year-2026" not in dests
    assert "quarter-2026-Q1" not in dests


def test_press_selects_bullet_journal_from_toml(tmp_path: Path):
    spec = Spec.from_path(Path("examples/nomad-bujo.toml"))
    assert spec.book == "bullet-journal"
    assert spec.device == "supernote-nomad"
    assert spec.bujo_index_pages == 2
    assert spec.bujo_collections == 24
    assert spec.habit_columns == 8
    assert spec.outline is True
    assert book_for(spec.book) is BulletJournal
    assert book_for("year-planner") is YearPlanner
    assert book_for("projects-notebook") is ProjectsNotebook
    assert book_for("engineering-notebook") is EngineeringNotebook
    assert not hasattr(spec, "days_per_page")
    assert not hasattr(spec, "dated_dailies")
    assert not hasattr(spec, "print_key")
    assert not hasattr(spec, "gutter_mm")

    jan = Spec(
        book="bullet-journal",
        months=(1,),
        habit_columns=spec.habit_columns,
        bujo_index_pages=spec.bujo_index_pages,
        bujo_collections=2,
    )
    out = tmp_path / "nomad-bujo.toml-jan.pdf"
    press(jan, out)
    dests = _named_dests(PdfReader(out))
    assert spec.bujo_key_dest in dests
    assert spec.dest_for_bujo_index(1) in dests
    assert spec.dest_for_bujo_index(2) in dests
    assert "2026-01-15" in dests


def test_bujo_unknown_toml_keys_fail_loudly():
    with pytest.raises(ConfigError, match="unknown bujo key 'pattern'"):
        Spec.from_mapping({"book": "bullet-journal", "bujo": {"pattern": "dotted"}})
    with pytest.raises(ConfigError, match="unknown bujo key 'habits'"):
        Spec.from_mapping({"book": "bullet-journal", "bujo": {"habits": True}})
    with pytest.raises(ConfigError, match="unknown bujo key 'days_per_page'"):
        Spec.from_mapping({"book": "bullet-journal", "bujo": {"days_per_page": 1}})
    with pytest.raises(ConfigError, match="book must be"):
        Spec.from_mapping({"book": "bujo"})


def test_january_plot_paints_key_and_gutter():
    plotter = RecordingPlotter()
    BulletJournal().plot(_JAN, plotter)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Key" in texts
    assert "task" in texts
    assert "Future log" in texts
    assert "January 2026" in texts
    assert "Habits · January 2026" in texts
    assert "Thu 1" in texts
    assert "Collections" in texts
    assert "Year Book" not in texts
    assert not any("monday weeks" in str(t).lower() for t in texts)
    assert "Q1" not in texts
    links = plotter.links()
    assert _JAN.bujo_key_dest in links
    assert _JAN.dest_for_month(1) in links
    assert "2026-01-01" in links
