from typing import get_args

import pytest
from parch.books import YearPlanner
from parch.components import CoverTitle, MonthGrid, TasksIndex, WeekStrip
from parch.devices.nomad import NOMAD
from parch.fonts import FontCatalog, JostRamp, TypeFamily, TypeInk, TypeRole, font_dir, jost_catalog
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    paint_cover,
    paint_header,
    paint_month_grid,
    paint_nav,
    paint_tasks_index,
    paint_week,
)
from parch.plotter import RecordingPlotter
from parch.plotter.fpdf2 import Fpdf2Plotter, resolve_weight
from parch.spec import Spec


def test_jost_weight_files_and_defaults():
    root = font_dir()
    assert (root / "Jost-400-Book.ttf").is_file()
    assert (root / "Jost-500-Medium.ttf").is_file()
    assert (root / "Jost-700-Bold.ttf").is_file()
    assert (root / "Jost-800-Heavy.ttf").is_file()
    assert (root / "LICENSE").is_file()
    assert (root / "AUTHORS").is_file()
    assert not (root / "LiberationSans-Regular.ttf").exists()
    assert not (root / "LiberationSerif-Regular.ttf").exists()
    assert resolve_weight("sans", False, None) == "book"
    assert resolve_weight("sans", True, None) == "bold"
    assert resolve_weight("serif", False, None) == "medium"
    assert resolve_weight("serif", True, None) == "medium"
    assert resolve_weight("serif", True, "heavy") == "heavy"
    Fpdf2Plotter(NOMAD)


def test_jost_catalog_is_four_cuts():
    catalog = jost_catalog()
    assert set(catalog.cuts) == {
        ("jost", "book"),
        ("jost", "medium"),
        ("jost", "bold"),
        ("jost", "heavy"),
    }
    assert catalog.register_name("jost", "heavy") == "jost:heavy"
    with pytest.raises(KeyError, match="family='jost' weight='hairline'"):
        catalog.path("jost", "hairline")


def test_jost_ramp_role_map():
    ramp = JostRamp()
    roles = get_args(getattr(TypeRole, "__value__", TypeRole))
    expected = {
        "cover_year": TypeInk(family="jost", weight="heavy", size=42),
        "cover_brow": TypeInk(family="jost", weight="medium", size=10),
        "cover_specs": TypeInk(family="jost", weight="book", size=8.2),
        "page_title": TypeInk(family="jost", weight="medium", size=11),
        "chrome": TypeInk(family="jost", weight="book", size=7.4),
        "nav_item": TypeInk(family="jost", weight="book", size=7.6),
        "nav_item_active": TypeInk(family="jost", weight="bold", size=7.6),
        "label": TypeInk(family="jost", weight="book", size=6.4),
        "section_heading": TypeInk(family="jost", weight="bold", size=6.4),
        "caption": TypeInk(family="jost", weight="book", size=5.8),
        "body": TypeInk(family="jost", weight="book", size=7.0),
        "weekday": TypeInk(family="jost", weight="book", size=6.6),
        "weekday_mini": TypeInk(family="jost", weight="book", size=4.3),
        "calendar_num": TypeInk(family="jost", weight="bold", size=8.5),
        "day_num": TypeInk(family="jost", weight="bold", size=11),
        "review_num": TypeInk(family="jost", weight="bold", size=9.2),
        "calendar_num_mini": TypeInk(family="jost", weight="book", size=5.3),
        "calendar_num_mini_on": TypeInk(family="jost", weight="bold", size=5.3),
        "chip_label": TypeInk(family="jost", weight="medium", size=7.0),
        "index_mark": TypeInk(family="jost", weight="medium", size=6.4),
        "habit_num": TypeInk(family="jost", weight="book", size=4.4),
        "habit_dow": TypeInk(family="jost", weight="book", size=4.4),
        "clone_mark": TypeInk(family="jost", weight="book", size=5.2),
    }
    assert set(roles) == set(expected)
    assert {role: ramp.ink(role) for role in expected} == expected
    assert all(ink.family == "jost" for ink in expected.values())
    assert set(ramp.catalog.cuts) == set(jost_catalog().cuts)


def _cover() -> CoverTitle:
    return CoverTitle(
        year=2026,
        subtitle="",
        device_name="nomad",
        cta_label="",
        cta_dest="year-2026",
    )


def _family(op: tuple[object, ...]) -> object:
    return op[10]


def test_cover_year_uses_jost_heavy_via_jost_ramp():
    plotter = RecordingPlotter()
    paint_cover(plotter, NOMAD, _cover(), ramp=JostRamp())
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == 42
    assert year[9] == "heavy"
    assert _family(year) == "jost"
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year Book")
    assert brow[9] == "medium"
    assert _family(brow) == "jost"
    specs = next(op for op in plotter.ops if op[0] == "text" and "monday weeks" in str(op[2]))
    assert specs[3] == 8.2
    assert specs[9] == "book"
    assert _family(specs) == "jost"
    assert specs[5] is False


def test_header_chrome_is_jost_book_via_jost_ramp():
    plotter = RecordingPlotter()
    paint_header(
        plotter,
        NOMAD,
        "Year",
        "2026",
        chip="01",
        ramp=JostRamp(),
    )
    title = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year")
    assert title[3] == 11
    assert title[9] == "medium"
    assert _family(title) == "jost"
    chip = next(op for op in plotter.ops if op[0] == "text" and op[2] == "01")
    assert chip[3] == 7.4
    assert chip[9] == "book"
    assert _family(chip) == "jost"
    meta = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert meta[3] == 7.4
    assert meta[9] == "book"
    assert _family(meta) == "jost"


def test_cover_honors_stub_ramp():
    class StubRamp:
        def __init__(self) -> None:
            self.roles: list[TypeRole] = []

        def ink(self, role: TypeRole) -> TypeInk:
            self.roles.append(role)
            return TypeInk(family="jost", weight="book", size=12)

    ramp = StubRamp()
    plotter = RecordingPlotter()
    paint_cover(plotter, NOMAD, _cover(), ramp=ramp)
    assert ramp.roles == ["cover_brow", "cover_year", "cover_specs"]
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == 12
    assert year[9] == "book"
    assert _family(year) == "jost"
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year Book")
    assert brow[3] == 12
    assert brow[9] == "book"
    assert _family(brow) == "jost"


def test_header_honors_stub_ramp():
    class StubRamp:
        def __init__(self) -> None:
            self.roles: list[TypeRole] = []

        def ink(self, role: TypeRole) -> TypeInk:
            self.roles.append(role)
            if role == "page_title":
                return TypeInk(family="jost", weight="bold", size=9)
            return TypeInk(family="jost", weight="book", size=6)

    ramp = StubRamp()
    plotter = RecordingPlotter()
    paint_header(
        plotter,
        NOMAD,
        "Projects",
        "2026",
        chip="01",
        ramp=ramp,
    )
    assert ramp.roles == ["page_title", "chrome"]
    title = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Projects")
    assert title[3] == 9
    assert title[9] == "bold"
    assert _family(title) == "jost"
    chip = next(op for op in plotter.ops if op[0] == "text" and op[2] == "01")
    assert chip[3] == 6
    assert chip[9] == "book"
    assert _family(chip) == "jost"
    meta = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert meta[3] == 6
    assert meta[9] == "book"
    assert _family(meta) == "jost"


def test_fonts_package_does_not_import_plotter():
    import parch.fonts as fonts

    assert "parch.plotter" not in fonts.__dict__
    assert fonts.JostRamp is JostRamp
    assert fonts.TypeInk is TypeInk
    assert fonts.TypeFamily is TypeFamily
    assert fonts.jost_catalog is jost_catalog
    assert fonts.FontCatalog is FontCatalog


def _text(ops: list, content: str) -> tuple:
    return next(op for op in ops if op[0] == "text" and op[2] == content)


def test_nav_resolves_via_roles():
    plotter = RecordingPlotter()
    paint_nav(
        plotter,
        NOMAD,
        (("Year", "year-2026"), ("Day", "2026-01-01")),
        "Year",
        ramp=JostRamp(),
    )
    year = _text(plotter.ops, "Year")
    day = _text(plotter.ops, "Day")
    assert year[3] == 7.6
    assert year[9] == "bold"
    assert _family(year) == "jost"
    assert year[5] is False
    assert day[3] == 7.6
    assert day[9] == "book"
    assert _family(day) == "jost"
    assert day[5] is False


def test_month_grid_resolves_via_roles():
    page = next(p for p in YearPlanner().pages(Spec(notes_pages=1)) if p.dest == "month-2026-07")
    grid = next(item for item in page.components if isinstance(item, MonthGrid))
    plotter = RecordingPlotter()
    paint_month_grid(plotter, well_rect(NOMAD), grid, ramp=JostRamp())
    dow = _text(plotter.ops, "M")
    assert dow[3] == 6.6
    assert dow[9] == "book"
    assert _family(dow) == "jost"
    assert dow[5] is False
    week = next(op for op in plotter.ops if op[0] == "text" and str(op[2]).startswith("W"))
    assert week[3] == 5.8
    assert week[9] == "book"
    assert _family(week) == "jost"
    day = _text(plotter.ops, "15")
    assert day[3] == 8.5
    assert day[9] == "bold"
    assert _family(day) == "jost"
    assert day[5] is False


def test_week_strip_resolves_via_roles():
    page = next(p for p in YearPlanner().pages(Spec(notes_pages=1)) if p.dest == "week-2026-W02")
    week = next(item for item in page.components if isinstance(item, WeekStrip))
    plotter = RecordingPlotter()
    paint_week(plotter, well_rect(NOMAD), week, ramp=JostRamp())
    dow = _text(plotter.ops, "Mon")
    assert dow[3] == 6.6
    assert dow[9] == "book"
    assert _family(dow) == "jost"
    num = _text(plotter.ops, "5")
    assert num[3] == 11
    assert num[9] == "bold"
    assert _family(num) == "jost"
    assert num[5] is False


def test_tasks_index_resolves_via_roles():
    page = next(
        p for p in YearPlanner().pages(Spec(notes_pages=1)) if p.dest == "tasks-index-2026-Q1"
    )
    index = next(item for item in page.components if isinstance(item, TasksIndex))
    plotter = RecordingPlotter()
    paint_tasks_index(plotter, well_rect(NOMAD), index, ramp=JostRamp())
    heading = _text(plotter.ops, "January")
    assert heading[3] == 6.4
    assert heading[9] == "bold"
    assert _family(heading) == "jost"
    assert heading[5] is False
    chip = _text(plotter.ops, "W01")
    assert chip[3] == 7.0
    assert chip[9] == "medium"
    assert _family(chip) == "jost"
    assert chip[5] is False


def test_nav_honors_stub_ramp():
    class StubRamp:
        def __init__(self) -> None:
            self.roles: list[TypeRole] = []

        def ink(self, role: TypeRole) -> TypeInk:
            self.roles.append(role)
            if role == "nav_item_active":
                return TypeInk(family="jost", weight="heavy", size=14)
            return TypeInk(family="jost", weight="book", size=5)

    ramp = StubRamp()
    plotter = RecordingPlotter()
    paint_nav(
        plotter,
        NOMAD,
        (("Year", "year-2026"), ("Day", "2026-01-01")),
        "Day",
        ramp=ramp,
    )
    assert ramp.roles == ["nav_item", "nav_item_active"]
    year = _text(plotter.ops, "Year")
    assert year[3] == 5
    assert year[9] == "book"
    assert _family(year) == "jost"
    day = _text(plotter.ops, "Day")
    assert day[3] == 14
    assert day[9] == "heavy"
    assert _family(day) == "jost"
