import pytest
from parch.components import CoverTitle
from parch.devices.nomad import NOMAD
from parch.fonts import (
    JostBesleyRamp,
    JostRamp,
    MartianBesleyRamp,
    TypeInk,
    TypeRole,
    font_dir,
    jost_besley_catalog,
    jost_catalog,
    martian_besley_catalog,
)
from parch.layouts.planner.painters import paint_cover, paint_header
from parch.plotter import RecordingPlotter
from parch.plotter.fpdf2 import Fpdf2Plotter, resolve_weight


def test_jost_weight_files_and_defaults():
    root = font_dir()
    assert (root / "Jost-400-Book.ttf").is_file()
    assert (root / "Jost-500-Medium.ttf").is_file()
    assert (root / "Jost-700-Bold.ttf").is_file()
    assert (root / "Jost-800-Heavy.ttf").is_file()
    assert (root / "LICENSE").is_file()
    assert not (root / "LiberationSans-Regular.ttf").exists()
    assert not (root / "LiberationSerif-Regular.ttf").exists()
    assert resolve_weight("sans", False, None) == "book"
    assert resolve_weight("sans", True, None) == "bold"
    assert resolve_weight("serif", False, None) == "medium"
    assert resolve_weight("serif", True, None) == "medium"
    assert resolve_weight("serif", True, "heavy") == "heavy"
    Fpdf2Plotter(NOMAD)


def test_besley_files_are_curated_not_maximal():
    root = font_dir()
    assert (root / "Besley-Regular.ttf").is_file()
    assert (root / "Besley-Bold.ttf").is_file()
    assert (root / "LICENSE-Besley").is_file()
    assert not (root / "Besley-Heavy.ttf").exists()
    assert not (root / "Besley-Medium.ttf").exists()
    dual = jost_besley_catalog()
    assert ("besley", "book") in dual.cuts
    assert ("besley", "bold") in dual.cuts
    assert ("besley", "heavy") not in dual.cuts
    assert ("besley", "medium") not in dual.cuts
    Fpdf2Plotter(NOMAD, catalog=dual)


def test_jost_catalog_is_four_cuts():
    catalog = jost_catalog()
    assert set(catalog.cuts) == {
        ("jost", "book"),
        ("jost", "medium"),
        ("jost", "bold"),
        ("jost", "heavy"),
    }
    assert catalog.register_name("jost", "heavy") == "jost:heavy"


def test_jost_ramp_role_map():
    ramp = JostRamp()
    assert ramp.ink("cover_year") == TypeInk(family="jost", weight="heavy", size=42)
    assert ramp.ink("cover_brow") == TypeInk(family="jost", weight="medium", size=10)
    assert ramp.ink("page_title") == TypeInk(family="jost", weight="medium", size=11)
    assert ramp.ink("chrome") == TypeInk(family="jost", weight="book", size=7.4)
    assert set(ramp.catalog.cuts) == set(jost_catalog().cuts)


def test_jost_besley_ramp_role_map():
    ramp = JostBesleyRamp()
    assert ramp.ink("cover_year") == TypeInk(family="besley", weight="bold", size=42)
    assert ramp.ink("cover_brow") == TypeInk(family="besley", weight="book", size=10)
    assert ramp.ink("page_title") == TypeInk(family="besley", weight="bold", size=11)
    assert ramp.ink("chrome") == TypeInk(family="jost", weight="book", size=7.4)
    assert ("besley", "heavy") not in ramp.catalog.cuts


def test_martian_files_are_curated_not_maximal():
    root = font_dir() / "martian-grotesk"
    assert (root / "MartianGrotesk-Regular.ttf").is_file()
    assert (root / "MartianGrotesk-Bold.ttf").is_file()
    assert (root / "OFL.txt").is_file()
    assert (root / "AUTHORS.txt").is_file()
    assert not (root / "MartianGrotesk-Medium.ttf").exists()
    assert not (root / "MartianGrotesk-Heavy.ttf").exists()
    trio = martian_besley_catalog()
    assert ("martian", "book") in trio.cuts
    assert ("martian", "bold") in trio.cuts
    assert ("martian", "medium") not in trio.cuts
    assert ("martian", "heavy") not in trio.cuts
    assert ("jost", "book") in trio.cuts
    assert ("besley", "bold") in trio.cuts
    assert ("martian", "book") not in jost_catalog().cuts
    assert ("martian", "book") not in jost_besley_catalog().cuts
    with pytest.raises(KeyError, match="family='martian' weight='medium'"):
        trio.path("martian", "medium")
    with pytest.raises(KeyError, match="family='martian' weight='heavy'"):
        trio.path("martian", "heavy")
    Fpdf2Plotter(NOMAD, catalog=trio)


def test_martian_besley_ramp_role_map():
    ramp = MartianBesleyRamp()
    assert ramp.ink("cover_year") == TypeInk(family="besley", weight="bold", size=42)
    assert ramp.ink("cover_brow") == TypeInk(family="besley", weight="book", size=10)
    assert ramp.ink("page_title") == TypeInk(family="besley", weight="bold", size=11)
    assert ramp.ink("chrome") == TypeInk(family="martian", weight="book", size=7.4)
    assert ("martian", "heavy") not in ramp.catalog.cuts
    assert set(ramp.catalog.cuts) == set(martian_besley_catalog().cuts)


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


def test_cover_year_uses_besley_bold_via_jost_besley_ramp():
    plotter = RecordingPlotter()
    paint_cover(plotter, NOMAD, _cover(), ramp=JostBesleyRamp())
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == 42
    assert year[9] == "bold"
    assert _family(year) == "besley"
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year Book")
    assert brow[9] == "book"
    assert _family(brow) == "besley"
    specs = next(op for op in plotter.ops if op[0] == "text" and "monday weeks" in str(op[2]))
    assert _family(specs) is None
    assert specs[6] == "sans"


def test_cover_year_uses_besley_bold_via_martian_besley_ramp():
    plotter = RecordingPlotter()
    paint_cover(plotter, NOMAD, _cover(), ramp=MartianBesleyRamp())
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == 42
    assert year[9] == "bold"
    assert _family(year) == "besley"
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year Book")
    assert brow[9] == "book"
    assert _family(brow) == "besley"


def test_header_chrome_is_martian_book_via_martian_besley_ramp():
    plotter = RecordingPlotter()
    paint_header(
        plotter,
        NOMAD,
        "Year",
        "2026",
        chip="01",
        ramp=MartianBesleyRamp(),
    )
    title = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year")
    assert title[3] == 11
    assert title[9] == "bold"
    assert _family(title) == "besley"
    chip = next(op for op in plotter.ops if op[0] == "text" and op[2] == "01")
    assert chip[3] == 7.4
    assert chip[9] == "book"
    assert _family(chip) == "martian"
    meta = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert meta[3] == 7.4
    assert meta[9] == "book"
    assert _family(meta) == "martian"


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
    assert ramp.roles == ["cover_brow", "cover_year"]
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
            return TypeInk(family="besley", weight="book", size=6)

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
    assert _family(chip) == "besley"
    meta = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert meta[3] == 6
    assert meta[9] == "book"
    assert _family(meta) == "besley"


def test_fonts_package_does_not_import_plotter():
    import parch.fonts as fonts

    assert "parch.plotter" not in fonts.__dict__
    assert fonts.JostBesleyRamp is JostBesleyRamp
    assert fonts.MartianBesleyRamp is MartianBesleyRamp
    assert fonts.TypeInk is TypeInk
    assert fonts.martian_besley_catalog is martian_besley_catalog
