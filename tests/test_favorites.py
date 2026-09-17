from pathlib import Path

import pytest

from parch.books import YearPlanner, outline_entries
from parch.components import FavoritesPage
from parch.devices.registry import NOMAD
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    FAVORITES_CAPTION,
    FAVORITES_ICONS,
    FAVORITES_TITLE,
    favorites_column_rows,
    favorites_head_seats,
    favorites_row_parts,
    favorites_seats,
    paint_favorites,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.sections.favorites import FavoritesSection
from parch.spec import Spec


def test_favorites_off_by_default():
    spec = Spec(notes_pages=1)
    dests = [page.dest for page in YearPlanner().pages(spec)]
    assert spec.favorites_pages == 0
    assert "favorites-2026" not in dests
    assert dests[:3] == ["cover", "year-2026", "quarter-2026-Q1"]
    assert FavoritesSection(spec).pages() == []


def test_favorites_after_annual_when_enabled():
    spec = Spec(notes_pages=1, favorites_pages=1)
    pages = YearPlanner().pages(spec)
    dests = [page.dest for page in pages]
    assert dests[:4] == ["cover", "year-2026", "favorites-2026", "quarter-2026-Q1"]
    page = next(p for p in pages if p.dest == "favorites-2026")
    assert page.kind == "favorites"
    assert page.title == "Favorites"
    sheet = next(item for item in page.components if isinstance(item, FavoritesPage))
    assert sheet.year == 2026
    assert strip_active(page.kind) == "Year"
    labels = [label for label, _ in strip_items(page)]
    assert "Favorites" not in labels
    assert labels == [
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
    ]


def test_favorites_seats_two_columns():
    well = well_rect(NOMAD)
    head, (left, right) = favorites_seats(well)
    assert head.y == pytest.approx(well.y)
    assert left.x == pytest.approx(well.x)
    assert right.right == pytest.approx(well.right)
    assert right.x > left.right
    title, caption = favorites_head_seats(head)
    assert title.x == pytest.approx(head.x)
    assert caption.right == pytest.approx(head.right)
    header, body = favorites_column_rows(left)
    assert header.y == pytest.approx(left.y)
    assert len(body) >= 8
    assert body[-1].bottom == pytest.approx(left.bottom)
    slash, name, icons = favorites_row_parts(header)
    assert slash.x == pytest.approx(header.x)
    assert icons.right == pytest.approx(header.right)
    assert name.x == pytest.approx(slash.right)
    assert name.right == pytest.approx(icons.x)


def test_favorites_paint_caption_slash_and_rules():
    page = FavoritesPage(year=2026)
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_favorites(plotter, well, page)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert FAVORITES_TITLE in texts
    for line in FAVORITES_CAPTION:
        assert line in texts
    assert texts.count("/") == 2
    assert FAVORITES_ICONS == (
        "camera",
        "book",
        "note",
        "utensils",
        "bag",
        "applause",
    )

    frames = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w > 40
    ]
    assert len(frames) == 2
    rules = [op for op in plotter.ops if op[0] == "line"]
    assert len(rules) > 40


def test_favorites_chrome_year_and_no_fav_tab():
    spec = Spec(notes_pages=1, favorites_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "favorites")
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Favorites" in texts
    assert "2026" in texts
    assert texts.count("Favorites") >= 1
    for label in (
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
    ):
        assert label in texts
    assert "Fav" not in texts
    assert page.dest == spec.favorites_dest


def test_favorites_toml_knobs():
    assert Spec.from_mapping({"favorites": True}).favorites_pages == 1
    assert Spec.from_mapping({"favorites": False}).favorites_pages == 0
    assert Spec.from_mapping({"favorites_pages": 1}).favorites_pages == 1
    assert Spec.from_mapping({}).favorites_pages == 0
    assert Spec.from_mapping({"favorites_pages": 1}).favorites_dest == "favorites-2026"
    example = Spec.from_path(Path("examples/favorites.toml"))
    assert example.favorites_pages == 1
    assert example.notes_pages == 0
    assert example.months == (1,)


def test_favorites_outline_after_annual():
    spec = Spec(months=(1,), notes_pages=0, favorites_pages=1, outline=True)
    pages = YearPlanner().pages(spec)
    dests = [dest for _title, dest in outline_entries(pages)]
    assert dests[:2] == [spec.year_dest, spec.favorites_dest]
