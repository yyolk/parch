import inspect
from dataclasses import fields

import pytest
from parch.components import CoverTitle
from parch.devices.nomad import NOMAD
from parch.fonts import (
    FontCatalog,
    JostRamp,
    TypeEmphasis,
    TypeFamily,
    TypeInk,
    TypeRef,
    TypeRole,
    TypeStep,
    font_dir,
    jost_catalog,
)
from parch.layouts.planner.painters import (
    paint_cover,
    paint_header,
    paint_month_grid,
    paint_nav,
    paint_schedule,
    paint_week,
    _paint_mini_month,
    _paint_project_ticket,
)
from parch.plotter import RecordingPlotter
from parch.plotter.fpdf2 import Fpdf2Plotter, resolve_weight
from parch.plotter import recording as recording_mod


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


def test_type_ref_is_frozen_without_family_or_weight():
    names = {item.name for item in fields(TypeRef)}
    assert names == {"step", "emphasis", "size"}
    ref = TypeRef(step="cover_year")
    assert ref.emphasis == "regular"
    assert ref.size is None
    with pytest.raises(AttributeError):
        ref.step = "chrome"  # type: ignore[misc]


def test_jost_ramp_resolve_roles_and_steps():
    ramp = JostRamp()
    assert ramp.resolve(TypeRef(step="cover_year")) == TypeInk(
        family="jost", weight="heavy", size=42
    )
    assert ramp.resolve(TypeRef(step="display")) == TypeInk(
        family="jost", weight="heavy", size=42
    )
    assert ramp.resolve(TypeRef(step="cover_brow")) == TypeInk(
        family="jost", weight="medium", size=10
    )
    assert ramp.resolve(TypeRef(step="page_title")) == TypeInk(
        family="jost", weight="medium", size=11
    )
    assert ramp.resolve(TypeRef(step="chrome")) == TypeInk(
        family="jost", weight="book", size=7.4
    )
    assert ramp.resolve(TypeRef(step="cover_specs")) == TypeInk(
        family="jost", weight="book", size=8.2
    )
    assert ramp.resolve(TypeRef(step="title", emphasis="strong")) == TypeInk(
        family="jost", weight="bold", size=11
    )
    assert ramp.resolve(TypeRef(step="caption", size=5.3)) == TypeInk(
        family="jost", weight="book", size=5.3
    )
    assert ramp.ink("cover_year") == ramp.resolve(TypeRef(step="cover_year"))
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


def _weight(op: tuple[object, ...]) -> object:
    return op[9]


class StubRamp:
    def __init__(self) -> None:
        self.refs: list[TypeRef] = []

    def resolve(self, ref: TypeRef) -> TypeInk:
        self.refs.append(ref)
        if ref.step == "page_title":
            return TypeInk(family="jost", weight="bold", size=9)
        return TypeInk(family="jost", weight="book", size=12)


def test_cover_year_is_heavy_via_ref_to_ink():
    plotter = RecordingPlotter(ramp=JostRamp())
    paint_cover(plotter, NOMAD, _cover())
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == 42
    assert _weight(year) == "heavy"
    assert _family(year) == "jost"
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year Book")
    assert _weight(brow) == "medium"
    assert _family(brow) == "jost"
    specs = next(op for op in plotter.ops if op[0] == "text" and "monday weeks" in str(op[2]))
    assert specs[3] == 8.2
    assert _weight(specs) == "book"
    assert _family(specs) == "jost"


def test_header_chrome_is_jost_book_via_ref():
    plotter = RecordingPlotter(ramp=JostRamp())
    paint_header(plotter, NOMAD, "Year", "2026", chip="01")
    title = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year")
    assert title[3] == 11
    assert _weight(title) == "medium"
    assert _family(title) == "jost"
    chip = next(op for op in plotter.ops if op[0] == "text" and op[2] == "01")
    assert chip[3] == 7.4
    assert _weight(chip) == "book"
    assert _family(chip) == "jost"
    meta = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert meta[3] == 7.4
    assert _weight(meta) == "book"
    assert _family(meta) == "jost"


def test_cover_honors_stub_ramp_resolve():
    ramp = StubRamp()
    plotter = RecordingPlotter(ramp=ramp)
    paint_cover(plotter, NOMAD, _cover())
    assert ramp.refs == [
        TypeRef(step="cover_brow"),
        TypeRef(step="cover_year"),
        TypeRef(step="cover_specs"),
    ]
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == 12
    assert _weight(year) == "book"
    assert _family(year) == "jost"


def test_header_honors_stub_ramp_resolve():
    ramp = StubRamp()
    plotter = RecordingPlotter(ramp=ramp)
    paint_header(plotter, NOMAD, "Projects", "2026", chip="01")
    assert ramp.refs == [TypeRef(step="page_title"), TypeRef(step="chrome")]
    title = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Projects")
    assert title[3] == 9
    assert _weight(title) == "bold"
    assert _family(title) == "jost"
    chip = next(op for op in plotter.ops if op[0] == "text" and op[2] == "01")
    assert chip[3] == 12
    assert _weight(chip) == "book"


def test_nav_uses_typeref_chrome():
    plotter = RecordingPlotter(ramp=JostRamp())
    paint_nav(plotter, NOMAD, (("Year", "year-2026"), ("Day", "2026-01-01")), "Year")
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year")
    day = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Day")
    assert year[3] == 7.6
    assert _weight(year) == "bold"
    assert _family(year) == "jost"
    assert day[3] == 7.6
    assert _weight(day) == "book"
    assert _family(day) == "jost"


def test_painters_and_recording_never_select_weight():
    migrated = (
        paint_cover,
        paint_header,
        paint_nav,
        paint_month_grid,
        paint_week,
        paint_schedule,
        _paint_project_ticket,
        _paint_mini_month,
    )
    banned = ("family=", "weight=", "face=", "bold=", "ramp.ink", ".ink(")
    for fn in migrated:
        src = inspect.getsource(fn)
        for token in banned:
            assert token not in src, f"{fn.__name__} still has {token}"
        assert "TypeRef(" in src
    rec_src = inspect.getsource(recording_mod.RecordingPlotter.text)
    assert "resolve_weight" not in rec_src
    assert "resolve_weight" not in recording_mod.__dict__
    params = inspect.signature(RecordingPlotter.text).parameters
    assert "ref" in params
    params = inspect.signature(Fpdf2Plotter.text).parameters
    assert "ref" in params


def test_fonts_package_does_not_import_plotter():
    import parch.fonts as fonts

    assert "parch.plotter" not in fonts.__dict__
    assert fonts.JostRamp is JostRamp
    assert fonts.TypeInk is TypeInk
    assert fonts.TypeRef is TypeRef
    assert fonts.TypeStep is TypeStep
    assert fonts.TypeRole is TypeRole
    assert fonts.TypeEmphasis is TypeEmphasis
    assert fonts.TypeFamily is TypeFamily
    assert fonts.jost_catalog is jost_catalog
    assert fonts.FontCatalog is FontCatalog
