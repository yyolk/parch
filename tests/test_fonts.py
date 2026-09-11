import inspect

import pytest
from parch.components import CoverTitle
from parch.devices.nomad import NOMAD
from parch.fonts import FontCatalog, JostRamp, TypeFamily, TypeInk, TypeRole, font_dir, jost_catalog
from parch.layouts.planner.painters import paint_cover, paint_header, paint_nav
from parch.plotter import RecordingPlotter
from parch.plotter.fpdf2 import Fpdf2Plotter


def test_jost_weight_files_and_plotter():
    root = font_dir()
    assert (root / "Jost-400-Book.ttf").is_file()
    assert (root / "Jost-500-Medium.ttf").is_file()
    assert (root / "Jost-700-Bold.ttf").is_file()
    assert (root / "Jost-800-Heavy.ttf").is_file()
    assert (root / "LICENSE").is_file()
    assert (root / "AUTHORS").is_file()
    assert not (root / "LiberationSans-Regular.ttf").exists()
    assert not (root / "LiberationSerif-Regular.ttf").exists()
    Fpdf2Plotter(NOMAD)


def test_fpdf2_has_no_resolve_weight_or_face():
    import parch.plotter.fpdf2 as fpdf2
    import parch.plotter.protocol as protocol

    assert not hasattr(fpdf2, "resolve_weight")
    assert not hasattr(protocol, "TextFace")
    params = inspect.signature(Fpdf2Plotter.text).parameters
    assert "ink" in params
    assert "face" not in params
    assert "bold" not in params
    assert "family" not in params
    assert "weight" not in params
    assert "size" not in params


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
    assert ramp.ink("cover_year") == TypeInk(family="jost", weight="heavy", size=42)
    assert ramp.ink("cover_brow") == TypeInk(family="jost", weight="medium", size=10)
    assert ramp.ink("page_title") == TypeInk(family="jost", weight="medium", size=11)
    assert ramp.ink("chrome") == TypeInk(family="jost", weight="book", size=7.4)
    assert ramp.ink("cover_specs") == TypeInk(family="jost", weight="book", size=8.2)
    assert ramp.ink("nav") == TypeInk(family="jost", weight="book", size=7.6)
    assert ramp.ink("nav_on") == TypeInk(family="jost", weight="bold", size=7.6)
    assert ramp.ink("body") == TypeInk(family="jost", weight="book", size=6.4)
    assert ramp.ink("emphasis") == TypeInk(family="jost", weight="bold", size=8.5)
    assert ramp.ink("mark") == TypeInk(family="jost", weight="medium", size=6.6)
    assert set(ramp.catalog.cuts) == set(jost_catalog().cuts)


def test_type_ink_at_resizes():
    ink = TypeInk(family="jost", weight="book", size=6.4)
    assert ink.at(6.4) is ink
    assert ink.at(5.4) == TypeInk(family="jost", weight="book", size=5.4)


def _cover() -> CoverTitle:
    return CoverTitle(
        year=2026,
        subtitle="",
        device_name="nomad",
        cta_label="",
        cta_dest="year-2026",
    )


def _ink(op: tuple[object, ...]) -> TypeInk:
    recorded = op[3]
    assert isinstance(recorded, TypeInk)
    return recorded


def test_cover_year_uses_jost_heavy_via_jost_ramp():
    plotter = RecordingPlotter()
    paint_cover(plotter, NOMAD, _cover(), ramp=JostRamp())
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert _ink(year) == TypeInk(family="jost", weight="heavy", size=42)
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year Book")
    assert _ink(brow) == TypeInk(family="jost", weight="medium", size=10)
    specs = next(op for op in plotter.ops if op[0] == "text" and "monday weeks" in str(op[2]))
    assert _ink(specs) == TypeInk(family="jost", weight="book", size=8.2)


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
    assert _ink(title) == TypeInk(family="jost", weight="medium", size=11)
    chip = next(op for op in plotter.ops if op[0] == "text" and op[2] == "01")
    assert _ink(chip) == TypeInk(family="jost", weight="book", size=7.4)
    meta = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert _ink(meta) == TypeInk(family="jost", weight="book", size=7.4)


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
    assert _ink(year) == TypeInk(family="jost", weight="book", size=12)
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year Book")
    assert _ink(brow) == TypeInk(family="jost", weight="book", size=12)
    specs = next(op for op in plotter.ops if op[0] == "text" and "monday weeks" in str(op[2]))
    assert _ink(specs) == TypeInk(family="jost", weight="book", size=12)


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
    assert _ink(title) == TypeInk(family="jost", weight="bold", size=9)
    chip = next(op for op in plotter.ops if op[0] == "text" and op[2] == "01")
    assert _ink(chip) == TypeInk(family="jost", weight="book", size=6)
    meta = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert _ink(meta) == TypeInk(family="jost", weight="book", size=6)


def test_nav_uses_ramp_roles():
    plotter = RecordingPlotter()
    paint_nav(
        plotter,
        NOMAD,
        (("Year", "year-2026"), ("Day", "2026-01-01")),
        "Year",
        ramp=JostRamp(),
    )
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year")
    day = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Day")
    assert _ink(year) == TypeInk(family="jost", weight="bold", size=7.6)
    assert _ink(day) == TypeInk(family="jost", weight="book", size=7.6)


def test_year_planner_text_ops_are_type_ink_only():
    from parch.books import YearPlanner
    from parch.spec import Spec

    plotter = RecordingPlotter()
    YearPlanner().plot(Spec(months=[1], day=1, notes_pages=0), plotter)
    texts = [op for op in plotter.ops if op[0] == "text"]
    assert texts
    for op in texts:
        ink = _ink(op)
        assert ink.family == "jost"
        assert ink.weight in {"book", "medium", "bold", "heavy"}
        assert len(op) == 7


def test_fonts_package_does_not_import_plotter():
    import parch.fonts as fonts

    assert "parch.plotter" not in fonts.__dict__
    assert fonts.JostRamp is JostRamp
    assert fonts.TypeInk is TypeInk
    assert fonts.TypeFamily is TypeFamily
    assert fonts.jost_catalog is jost_catalog
    assert fonts.FontCatalog is FontCatalog
