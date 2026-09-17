from pathlib import Path

import pytest

from parch.books import YearPlanner, outline_entries
from parch.components import FavoritesPage
from parch.devices.registry import NOMAD
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    FAVORITES_COLS,
    FAVORITES_GRID_ROWS,
    FAVORITES_ICON_GAP,
    FAVORITES_ICON_SCALE,
    FAVORITES_ICON_STROKE,
    FAVORITES_ICONS,
    HAIR,
    INK,
    WASH,
    favorites_body_rows,
    favorites_card_parts,
    favorites_header_parts,
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


def test_favorites_seats_grid():
    well = well_rect(NOMAD)
    seats = favorites_seats(well)
    assert FAVORITES_COLS == 2
    assert FAVORITES_GRID_ROWS == 3
    assert len(seats) == 6
    assert seats[0].x == pytest.approx(well.x)
    assert seats[0].y == pytest.approx(well.y)
    assert seats[1].right == pytest.approx(well.right)
    assert seats[1].x > seats[0].right
    assert seats[2].y > seats[0].bottom
    assert seats[5].right == pytest.approx(well.right)
    assert seats[5].bottom == pytest.approx(well.bottom)
    header, body = favorites_card_parts(seats[0])
    assert header.y == pytest.approx(seats[0].y)
    assert body.bottom == pytest.approx(seats[0].bottom)
    slash, name, icons = favorites_header_parts(header)
    assert slash.y == pytest.approx(name.y)
    assert icons.y == pytest.approx(slash.y)
    assert slash.h == pytest.approx(name.h)
    assert icons.h == pytest.approx(slash.h)
    assert name.x == pytest.approx(slash.right)
    assert icons.x == pytest.approx(name.right)
    assert icons.w > name.w
    assert icons.w >= 20
    write = favorites_body_rows(body)
    assert 3 <= len(write) <= 5
    assert write[0].y > header.bottom
    assert write[0].x > seats[0].x
    assert write[0].right < seats[0].right


def test_favorites_paint_cards_slash_and_icons():
    page = FavoritesPage(year=2026)
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_favorites(plotter, well, page)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Favorites" not in texts
    assert "five stars" not in " ".join(texts)
    assert "rankings" not in " ".join(texts)
    assert texts.count("/") == 6
    assert FAVORITES_ICONS == (
        "camera",
        "book",
        "note",
        "utensils",
        "bag",
        "applause",
    )
    assert 1.6 <= FAVORITES_ICON_GAP <= 2.0
    assert 0.70 <= FAVORITES_ICON_SCALE <= 0.78
    assert FAVORITES_ICON_STROKE > HAIR

    frames = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[2]
        and not op[3]
        and op[1].w > 40
        and op[6] == pytest.approx(INK)
    ]
    assert len(frames) == 6
    cages = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[2]
        and not op[3]
        and 4.0 < op[1].w < 8.0
        and 4.0 < op[1].h < 8.0
    ]
    assert cages == []
    washes = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[3] and not op[2] and op[5] == pytest.approx(WASH)
    ]
    assert len(washes) == 6
    header_rules = [
        op
        for op in plotter.ops
        if op[0] == "line"
        and op[5] == pytest.approx(HAIR)
        and op[6] == pytest.approx(INK)
    ]
    assert len(header_rules) == 6
    rules = [op for op in plotter.ops if op[0] == "line"]
    assert len(rules) > 20


def test_favorites_chrome_year_and_no_fav_tab():
    spec = Spec(notes_pages=1, favorites_pages=1)
    page = next(p for p in YearPlanner().pages(spec) if p.kind == "favorites")
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("Favorites") == 1
    assert "2026" in texts
    assert "five stars" not in " ".join(texts)
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
