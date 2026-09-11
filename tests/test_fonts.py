from datetime import date
from typing import get_args

import pytest
from parch.components import CoverTitle, WeekDay, WeekStrip
from parch.devices.nomad import NOMAD
from parch.fonts import (
    BoundRamp,
    FontCatalog,
    JostRamp,
    TypeFamily,
    TypeInk,
    TypeStep,
    font_dir,
    jost_catalog,
    jost_pagekind_table,
)
from parch.geom import Rect
from parch.layouts.planner.painters import paint_cover, paint_header, paint_week
from parch.plotter import RecordingPlotter
from parch.plotter.fpdf2 import Fpdf2Plotter, resolve_weight
from parch.sections.page import PageKind


def _alias_args(alias: object) -> tuple[object, ...]:
    return get_args(getattr(alias, "__value__", alias))


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


def test_pagekind_table_is_complete_and_jost_only():
    table = jost_pagekind_table()
    kinds = _alias_args(PageKind)
    steps = _alias_args(TypeStep)
    assert set(table) == set(kinds)
    for kind in kinds:
        row = table[kind]
        assert set(row) == set(steps)
        for step in steps:
            ink = row[step]
            assert ink.family == "jost"
            assert ink.weight in {"book", "medium", "bold", "heavy"}
            assert ink.size > 0


def test_pagekind_table_locked_values():
    table = jost_pagekind_table()
    assert table["cover"]["display"] == TypeInk(family="jost", weight="heavy", size=42)
    assert table["cover"]["brow"] == TypeInk(family="jost", weight="medium", size=10)
    assert table["cover"]["body"] == TypeInk(family="jost", weight="book", size=8.2)
    assert table["cover"]["title"] == TypeInk(family="jost", weight="medium", size=10)
    assert table["cover"]["chrome"] == TypeInk(family="jost", weight="book", size=7.4)
    assert table["annual"]["title"] == TypeInk(family="jost", weight="medium", size=11)
    assert table["annual"]["chrome"] == TypeInk(family="jost", weight="book", size=7.4)
    assert table["annual"]["body"] == TypeInk(family="jost", weight="book", size=6.4)
    assert table["month"]["body"] == TypeInk(family="jost", weight="bold", size=8.5)
    assert table["weekly"]["body"] == TypeInk(family="jost", weight="bold", size=11)
    assert table["daily"]["body"] == TypeInk(family="jost", weight="book", size=7.0)
    assert table["projects_index"]["body"] == TypeInk(family="jost", weight="bold", size=6.6)
    assert table["project"]["body"] == TypeInk(family="jost", weight="bold", size=6.6)


def test_daily_body_differs_from_week_body():
    ramp = JostRamp()
    daily = ramp.for_page("daily").ink("body")
    week = ramp.for_page("weekly").ink("body")
    assert daily != week
    assert daily.size != week.size
    table = jost_pagekind_table()
    assert table["daily"]["body"] != table["weekly"]["body"]


def test_for_page_returns_bound_ramp_not_threadlocal():
    ramp = JostRamp()
    daily = ramp.for_page("daily")
    week = ramp.for_page("weekly")
    assert isinstance(daily, BoundRamp)
    assert daily.kind == "daily"
    assert week.kind == "weekly"
    assert daily is not week
    assert daily.ink("body") != week.ink("body")
    rebound = daily.for_page("weekly")
    assert rebound.kind == "weekly"
    assert rebound.ink("body") == week.ink("body")
    assert daily.ink("body") == ramp.for_page("daily").ink("body")


def test_ink_override_does_not_mutate_table():
    bound = JostRamp().for_page("daily")
    base = bound.ink("body")
    tweaked = bound.ink("body", size=9.5, weight="bold")
    assert tweaked == TypeInk(family="jost", weight="bold", size=9.5)
    assert bound.ink("body") == base
    assert jost_pagekind_table()["daily"]["body"] == base


def test_unbound_ink_uses_cover_display_and_annual_interior():
    ramp = JostRamp()
    assert ramp.ink("display") == TypeInk(family="jost", weight="heavy", size=42)
    assert ramp.ink("brow") == TypeInk(family="jost", weight="medium", size=10)
    assert ramp.ink("title") == TypeInk(family="jost", weight="medium", size=11)
    assert ramp.ink("chrome") == TypeInk(family="jost", weight="book", size=7.4)
    assert ramp.ink("body") == TypeInk(family="jost", weight="book", size=6.4)
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


def test_cover_uses_bound_cover_row():
    plotter = RecordingPlotter()
    paint_cover(plotter, NOMAD, _cover(), ramp=JostRamp().for_page("cover"))
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == 42
    assert year[9] == "heavy"
    assert _family(year) == "jost"
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year Book")
    assert brow[9] == "medium"
    assert brow[3] == 10
    assert _family(brow) == "jost"
    specs = next(op for op in plotter.ops if op[0] == "text" and "monday weeks" in str(op[2]))
    assert specs[3] == 8.2
    assert specs[9] == "book"
    assert _family(specs) == "jost"


def test_header_chrome_is_jost_book_via_bound_ramp():
    plotter = RecordingPlotter()
    paint_header(
        plotter,
        NOMAD,
        "Year",
        "2026",
        chip="01",
        ramp=JostRamp().for_page("annual"),
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
            self.steps: list[TypeStep] = []

        def ink(self, step: TypeStep, *, weight=None, size=None) -> TypeInk:
            self.steps.append(step)
            return TypeInk(family="jost", weight="book", size=12)

        def for_page(self, kind: PageKind) -> "StubRamp":
            return self

    ramp = StubRamp()
    plotter = RecordingPlotter()
    paint_cover(plotter, NOMAD, _cover(), ramp=ramp)
    assert ramp.steps == ["brow", "display", "body"]
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
            self.steps: list[TypeStep] = []

        def ink(self, step: TypeStep, *, weight=None, size=None) -> TypeInk:
            self.steps.append(step)
            if step == "title":
                return TypeInk(family="jost", weight="bold", size=9)
            return TypeInk(family="jost", weight="book", size=6)

        def for_page(self, kind: PageKind) -> "StubRamp":
            return self

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
    assert ramp.steps == ["title", "chrome"]
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


def test_week_painter_uses_bound_body_not_daily_body():
    monday = date(2026, 7, 13)
    week = WeekStrip(
        iso_year=2026,
        iso_week=29,
        monday=monday,
        sunday=date(2026, 7, 19),
        days=tuple(
            WeekDay(
                day=date(2026, 7, 13 + i),
                weekday_label=("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")[i],
                in_month=True,
                dest=f"2026-07-{13 + i:02d}",
            )
            for i in range(7)
        ),
    )
    daily_ramp = JostRamp().for_page("daily")
    week_ramp = JostRamp().for_page("weekly")
    daily_plot = RecordingPlotter()
    week_plot = RecordingPlotter()
    paint_week(daily_plot, Rect(4, 20, 110, 90), week, ramp=daily_ramp)
    paint_week(week_plot, Rect(4, 20, 110, 90), week, ramp=week_ramp)
    daily_num = next(op for op in daily_plot.ops if op[0] == "text" and op[2] == "13")
    week_num = next(op for op in week_plot.ops if op[0] == "text" and op[2] == "13")
    assert daily_num[3] == daily_ramp.ink("body").size
    assert week_num[3] == week_ramp.ink("body").size
    assert daily_num[3] != week_num[3]
    assert week_num[9] == "bold"
    assert daily_num[9] == "book"
    assert _family(week_num) == "jost"


def test_fonts_package_does_not_import_plotter():
    import parch.fonts as fonts

    assert "parch.plotter" not in fonts.__dict__
    assert fonts.JostRamp is JostRamp
    assert fonts.TypeInk is TypeInk
    assert fonts.TypeFamily is TypeFamily
    assert fonts.jost_catalog is jost_catalog
    assert fonts.FontCatalog is FontCatalog
    assert fonts.BoundRamp is BoundRamp
    assert fonts.jost_pagekind_table is jost_pagekind_table
