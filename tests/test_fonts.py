from pathlib import Path
from typing import get_args

import pytest
from parch.books import YearPlanner
from parch.components import CoverTitle
from parch.devices.nomad import NOMAD
from parch.fonts import (
    JOST_ROLES,
    FontCatalog,
    JostRamp,
    TypeFamily,
    TypeInk,
    TypeRole,
    font_dir,
    jost_catalog,
)
from parch.layouts.planner.painters import paint_cover, paint_header
from parch.plotter import RecordingPlotter
from parch.plotter.fpdf2 import Fpdf2Plotter, resolve_weight
from parch.spec import Spec

# Frozen Thesis J table — lock sizes/weights, not speculative scale names.
_FROZEN: dict[TypeRole, TypeInk] = {
    "cover_year": TypeInk(family="jost", weight="heavy", size=42),
    "cover_brow": TypeInk(family="jost", weight="medium", size=10),
    "cover_spec": TypeInk(family="jost", weight="book", size=8.2),
    "page_title": TypeInk(family="jost", weight="medium", size=11),
    "week_day": TypeInk(family="jost", weight="bold", size=11),
    "review_day": TypeInk(family="jost", weight="bold", size=9.2),
    "month_day": TypeInk(family="jost", weight="bold", size=8.5),
    "nav": TypeInk(family="jost", weight="book", size=7.6),
    "nav_on": TypeInk(family="jost", weight="bold", size=7.6),
    "chrome": TypeInk(family="jost", weight="book", size=7.4),
    "tasks_week": TypeInk(family="jost", weight="medium", size=7.2),
    "hour": TypeInk(family="jost", weight="book", size=7.0),
    "review_week": TypeInk(family="jost", weight="medium", size=7.0),
    "weekday": TypeInk(family="jost", weight="book", size=6.6),
    "project_stub": TypeInk(family="jost", weight="medium", size=6.6),
    "label": TypeInk(family="jost", weight="book", size=6.4),
    "cal_month": TypeInk(family="jost", weight="bold", size=6.4),
    "week_range": TypeInk(family="jost", weight="book", size=6.2),
    "index_month": TypeInk(family="jost", weight="bold", size=6.2),
    "meeting_stub": TypeInk(family="jost", weight="medium", size=6.2),
    "cue": TypeInk(family="jost", weight="book", size=5.8),
    "review_dow": TypeInk(family="jost", weight="book", size=5.6),
    "status": TypeInk(family="jost", weight="book", size=5.4),
    "cal_day": TypeInk(family="jost", weight="book", size=5.3),
    "cal_day_on": TypeInk(family="jost", weight="bold", size=5.3),
    "priority_mark": TypeInk(family="jost", weight="book", size=5.2),
    "habit_day": TypeInk(family="jost", weight="book", size=4.4),
    "cal_dow": TypeInk(family="jost", weight="book", size=4.3),
}


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


def test_jost_ramp_role_table_is_frozen():
    ramp = JostRamp()
    assert set(get_args(TypeRole.__value__)) == set(_FROZEN) == set(JOST_ROLES)
    assert JOST_ROLES == _FROZEN
    for role, ink in _FROZEN.items():
        assert ramp.ink(role) == ink
        assert ink.family == "jost"
    assert set(ramp.catalog.cuts) == set(jost_catalog().cuts)


def test_mvp_text_ops_use_only_frozen_jost_roles():
    """Every MVP text op is family+weight+size from the frozen table. No leftovers."""
    spec = Spec.from_path(Path("examples/mvp.toml"))
    plotter = RecordingPlotter()
    YearPlanner().plot(spec, plotter)
    inks = {(ink.size, ink.weight, ink.family) for ink in _FROZEN.values()}
    seen: set[tuple[float, str, str]] = set()
    for op in plotter.ops:
        if op[0] != "text":
            continue
        size, _align, bold, _face, _gray, _smcp, weight, family = op[3:11]
        assert family == "jost"
        assert weight is not None
        key = (float(size), weight, family)
        assert key in inks, f"unfrozen text {op[2]!r} size={size} weight={weight}"
        seen.add(key)
    assert seen == inks, f"unused roles: {inks - seen}"


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
    assert ramp.roles == ["cover_brow", "cover_year", "cover_spec"]
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
    assert fonts.JOST_ROLES is JOST_ROLES
