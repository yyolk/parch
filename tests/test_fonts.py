import parch.plotter.fpdf2 as fpdf2
import pytest
from parch.components import CoverTitle
from parch.devices.nomad import NOMAD
from parch.fonts import (
    FontCatalog,
    JostRamp,
    TypeEmphasis,
    TypeFamily,
    TypeInk,
    TypeRole,
    TypeSlot,
    font_dir,
    jost_catalog,
)
from parch.layouts.planner.painters import paint_cover, paint_header, paint_nav
from parch.plotter import RecordingPlotter
from parch.plotter.fpdf2 import Fpdf2Plotter


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
    assert not hasattr(fpdf2, "resolve_weight")
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
    assert ramp.ink("cover_year") == TypeInk(family="jost", weight="heavy", size=42)
    assert ramp.ink("cover_brow") == TypeInk(family="jost", weight="medium", size=10)
    assert ramp.ink("page_title") == TypeInk(family="jost", weight="medium", size=11)
    assert ramp.ink("chrome") == TypeInk(family="jost", weight="book", size=7.4)
    assert set(ramp.catalog.cuts) == set(jost_catalog().cuts)


def test_jost_ramp_slot_table():
    ramp = JostRamp()
    table = (
        (TypeSlot.COPY, TypeEmphasis.REGULAR, "book"),
        (TypeSlot.COPY, TypeEmphasis.STRONG, "bold"),
        (TypeSlot.MARK, TypeEmphasis.REGULAR, "medium"),
        (TypeSlot.MARK, TypeEmphasis.STRONG, "medium"),
    )
    for slot, emphasis, weight in table:
        ink = ramp.resolve_slot(slot, emphasis, 8.2)
        assert ink == TypeInk(family="jost", weight=weight, size=8.2)
    mark = ramp.resolve_slot(TypeSlot.MARK, TypeEmphasis.STRONG, 6.6)
    assert mark.weight == "medium"
    copy_regular = ramp.resolve_slot(TypeSlot.COPY, TypeEmphasis.REGULAR, 7.6)
    copy_strong = ramp.resolve_slot(TypeSlot.COPY, TypeEmphasis.STRONG, 7.6)
    assert copy_regular.weight == "book"
    assert copy_strong.weight == "bold"
    assert TypeSlot.COPY == "copy"
    assert TypeSlot.MARK == "mark"
    assert set(TypeSlot) == {TypeSlot.COPY, TypeSlot.MARK}


def _cover() -> CoverTitle:
    return CoverTitle(
        year=2026,
        subtitle="",
        device_name="nomad",
        cta_label="",
        cta_dest="year-2026",
    )


def _family(op: tuple[object, ...]) -> object:
    return op[8]


def _weight(op: tuple[object, ...]) -> object:
    return op[7]


def test_cover_year_uses_jost_heavy_via_jost_ramp():
    plotter = RecordingPlotter()
    paint_cover(plotter, NOMAD, _cover(), ramp=JostRamp())
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == 42
    assert _weight(year) == "heavy"
    assert _family(year) == "jost"
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year Book")
    assert _weight(brow) == "medium"
    assert _family(brow) == "jost"
    specs = next(op for op in plotter.ops if op[0] == "text" and "monday weeks" in str(op[2]))
    assert _family(specs) == "jost"
    assert _weight(specs) == "book"
    assert specs[3] == 8.2


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


def test_cover_honors_stub_ramp():
    class StubRamp:
        def __init__(self) -> None:
            self.roles: list[TypeRole] = []
            self.slots: list[tuple[TypeSlot, TypeEmphasis, float]] = []

        def ink(self, role: TypeRole) -> TypeInk:
            self.roles.append(role)
            return TypeInk(family="jost", weight="book", size=12)

        def resolve_slot(self, slot: TypeSlot, emphasis: TypeEmphasis, size: float) -> TypeInk:
            self.slots.append((slot, emphasis, size))
            return TypeInk(family="jost", weight="book", size=size)

    ramp = StubRamp()
    plotter = RecordingPlotter()
    paint_cover(plotter, NOMAD, _cover(), ramp=ramp)
    assert ramp.roles == ["cover_brow", "cover_year"]
    assert ramp.slots == [(TypeSlot.COPY, TypeEmphasis.REGULAR, 8.2)]
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == 12
    assert _weight(year) == "book"
    assert _family(year) == "jost"
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year Book")
    assert brow[3] == 12
    assert _weight(brow) == "book"
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
    assert _weight(title) == "bold"
    assert _family(title) == "jost"
    chip = next(op for op in plotter.ops if op[0] == "text" and op[2] == "01")
    assert chip[3] == 6
    assert _weight(chip) == "book"
    assert _family(chip) == "jost"
    meta = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert meta[3] == 6
    assert _weight(meta) == "book"
    assert _family(meta) == "jost"


def test_nav_uses_resolve_slot():
    class StubRamp:
        catalog = jost_catalog()

        def __init__(self) -> None:
            self.slots: list[tuple[TypeSlot, TypeEmphasis, float]] = []

        def ink(self, role: TypeRole) -> TypeInk:
            return TypeInk(family="jost", weight="book", size=7)

        def resolve_slot(self, slot: TypeSlot, emphasis: TypeEmphasis, size: float) -> TypeInk:
            self.slots.append((slot, emphasis, size))
            weight = "heavy" if emphasis is TypeEmphasis.STRONG else "book"
            return TypeInk(family="jost", weight=weight, size=size)

    ramp = StubRamp()
    plotter = RecordingPlotter()
    paint_nav(plotter, NOMAD, (("Year", "year-2026"), ("Day", "2026-01-01")), "Year", ramp=ramp)
    assert ramp.slots == [
        (TypeSlot.COPY, TypeEmphasis.STRONG, 7.6),
        (TypeSlot.COPY, TypeEmphasis.REGULAR, 7.6),
    ]
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year")
    assert _weight(year) == "heavy"
    day = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Day")
    assert _weight(day) == "book"


def test_fonts_package_does_not_import_plotter():
    import parch.fonts as fonts

    assert "parch.plotter" not in fonts.__dict__
    assert fonts.JostRamp is JostRamp
    assert fonts.TypeInk is TypeInk
    assert fonts.TypeSlot is TypeSlot
    assert fonts.TypeEmphasis is TypeEmphasis
    assert fonts.TypeFamily is TypeFamily
    assert fonts.jost_catalog is jost_catalog
    assert fonts.FontCatalog is FontCatalog
