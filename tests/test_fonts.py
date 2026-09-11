import pytest
from parch.components import CoverTitle
from parch.devices.nomad import NOMAD
from parch.fonts import (
    ROLE_WEIGHTS,
    SIZE_BANDS,
    FontCatalog,
    JostRamp,
    TypeFamily,
    TypeInk,
    TypeRole,
    band_weight,
    cut_for,
    font_dir,
    jost_catalog,
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


def test_size_band_table():
    assert SIZE_BANDS == ((30.0, "heavy"), (11.0, "medium"), (0.0, "book"))
    assert band_weight(42) == "heavy"
    assert band_weight(30) == "heavy"
    assert band_weight(29.9) == "medium"
    assert band_weight(11) == "medium"
    assert band_weight(10.9) == "book"
    assert band_weight(7.4) == "book"
    assert band_weight(0) == "book"


def test_cut_for_bands_and_bold():
    assert cut_for(42) == "heavy"
    assert cut_for(30) == "heavy"
    assert cut_for(11) == "medium"
    assert cut_for(10) == "book"
    assert cut_for(8.2) == "book"
    # bold forces Bold only inside body bands (medium / book)
    assert cut_for(10, bold=True) == "bold"
    assert cut_for(11, bold=True) == "bold"
    assert cut_for(29.9, bold=True) == "bold"
    assert cut_for(30, bold=True) == "heavy"
    assert cut_for(42, bold=True) == "heavy"


def test_role_overrides_ignore_size_and_bold():
    assert dict(ROLE_WEIGHTS) == {
        "cover_year": "heavy",
        "page_title": "medium",
        "chrome": "book",
    }
    assert cut_for(8, role="cover_year") == "heavy"
    assert cut_for(8, role="cover_year", bold=True) == "heavy"
    assert cut_for(42, role="page_title") == "medium"
    assert cut_for(6, role="page_title", bold=True) == "medium"
    assert cut_for(42, role="chrome") == "book"
    assert cut_for(11, role="chrome", bold=True) == "book"


def test_jost_ramp_is_explicit_sizeband_object():
    ramp = JostRamp()
    assert ramp.bands is SIZE_BANDS
    assert ramp.roles is ROLE_WEIGHTS
    assert ramp.ink(42) == TypeInk(family="jost", weight="heavy", size=42)
    assert ramp.ink(11) == TypeInk(family="jost", weight="medium", size=11)
    assert ramp.ink(7.4) == TypeInk(family="jost", weight="book", size=7.4)
    assert ramp.ink(8.5, bold=True) == TypeInk(family="jost", weight="bold", size=8.5)
    assert ramp.ink(42, role="cover_year") == TypeInk(family="jost", weight="heavy", size=42)
    assert ramp.ink(11, role="page_title") == TypeInk(family="jost", weight="medium", size=11)
    assert ramp.ink(7.4, role="chrome") == TypeInk(family="jost", weight="book", size=7.4)
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


def test_cover_year_uses_role_heavy_brow_uses_size_band():
    plotter = RecordingPlotter()
    paint_cover(plotter, NOMAD, _cover(), ramp=JostRamp())
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == 42
    assert year[9] == "heavy"
    assert _family(year) == "jost"
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year Book")
    assert brow[3] == 10
    assert brow[9] == "book"
    assert _family(brow) == "jost"
    specs = next(op for op in plotter.ops if op[0] == "text" and "monday weeks" in str(op[2]))
    assert specs[3] == 8.2
    assert specs[9] == "book"
    assert _family(specs) == "jost"


def test_header_roles_page_title_and_chrome():
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
            self.calls: list[tuple[float, TypeRole | None, bool]] = []

        def ink(
            self, size: float, *, role: TypeRole | None = None, bold: bool = False
        ) -> TypeInk:
            self.calls.append((size, role, bold))
            return TypeInk(family="jost", weight="book", size=12)

    ramp = StubRamp()
    plotter = RecordingPlotter()
    paint_cover(plotter, NOMAD, _cover(), ramp=ramp)
    assert ramp.calls == [(10, None, False), (42, "cover_year", False), (8.2, None, False)]
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
            self.calls: list[tuple[float, TypeRole | None, bool]] = []

        def ink(
            self, size: float, *, role: TypeRole | None = None, bold: bool = False
        ) -> TypeInk:
            self.calls.append((size, role, bold))
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
    assert ramp.calls == [(11, "page_title", False), (7.4, "chrome", False), (7.4, "chrome", False)]
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
    assert fonts.SIZE_BANDS is SIZE_BANDS
    assert fonts.cut_for is cut_for
