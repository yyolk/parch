from pathlib import Path

import pytest
from parch.books import YearPlanner
from parch.components import CoverTitle
from parch.devices.nomad import NOMAD, NOMAD_TYPE_OVERLAY
from parch.fonts import (
    EffectiveRamp,
    FontCatalog,
    JOST_FAMILY_OVERLAY,
    JostRamp,
    TypeFamily,
    TypeInk,
    TypeOverlay,
    TypePatch,
    TypeRole,
    apply_overlay,
    bind_ramp,
    compose_overlays,
    font_dir,
    jost_catalog,
)
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.painters import paint_cover, paint_header
from parch.plotter import RecordingPlotter
from parch.plotter.fpdf2 import Fpdf2Plotter, resolve_weight
from parch.press import press
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
    assert ramp.ink("cover_year") == TypeInk(family="jost", weight="heavy", size=42)
    assert ramp.ink("cover_brow") == TypeInk(family="jost", weight="medium", size=10)
    assert ramp.ink("page_title") == TypeInk(family="jost", weight="medium", size=11)
    assert ramp.ink("chrome") == TypeInk(family="jost", weight="book", size=7.4)
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
    assert _family(specs) is None
    assert specs[6] == "sans"


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
    assert fonts.EffectiveRamp is EffectiveRamp
    assert fonts.TypeOverlay is TypeOverlay
    assert fonts.TypePatch is TypePatch
    assert fonts.JOST_FAMILY_OVERLAY is JOST_FAMILY_OVERLAY


def test_overlay_explicit_size_keeps_default_weight_and_family():
    patch = TypePatch(size=9.0)
    base = TypeInk(family="jost", weight="book", size=7.4)
    assert apply_overlay(base, patch) == TypeInk(family="jost", weight="book", size=9.0)
    assert apply_overlay(base, None) == base


def test_overlay_explicit_weight_keeps_default_size_and_family():
    patch = TypePatch(weight="bold")
    base = TypeInk(family="jost", weight="book", size=7.4)
    assert apply_overlay(base, patch) == TypeInk(family="jost", weight="bold", size=7.4)


def test_family_overlay_wins_when_present():
    """Family overlay wins; catalog may map the key to a Jost cut (no new files)."""
    catalog = FontCatalog(
        {
            **dict(jost_catalog().cuts),
            ("future", "book"): font_dir() / "Jost-400-Book.ttf",
        }
    )
    ramp = EffectiveRamp(
        overlay=TypeOverlay(chrome=TypePatch(family="future")),
        catalog=catalog,
    )
    ink = ramp.ink("chrome")
    assert ink.family == "future"
    assert ink.weight == "book"
    assert ink.size == 7.4
    assert catalog.path("future", "book").name == "Jost-400-Book.ttf"


def test_missing_family_keeps_default():
    catalog = FontCatalog(
        {
            **dict(jost_catalog().cuts),
            ("future", "book"): font_dir() / "Jost-400-Book.ttf",
        }
    )
    ramp = EffectiveRamp(
        overlay=TypeOverlay(chrome=TypePatch(size=9.0)),
        catalog=catalog,
    )
    assert ramp.ink("chrome") == TypeInk(family="jost", weight="book", size=9.0)
    assert ramp.ink("page_title") == TypeInk(family="jost", weight="medium", size=11)


def test_explicit_jost_family_overlay_matches_default():
    ramp = EffectiveRamp(overlay=TypeOverlay(cover_year=TypePatch(family="jost")))
    assert ramp.ink("cover_year") == TypeInk(family="jost", weight="heavy", size=42)
    assert ramp.ink("chrome") == JostRamp().ink("chrome")


def test_unknown_family_fails_at_catalog():
    """TypePatch does not pre-validate family; catalog.path is the closed set."""
    ramp = EffectiveRamp(overlay=TypeOverlay(cover_year=TypePatch(family="besley")))
    with pytest.raises(KeyError, match="family='besley'"):
        ramp.ink("cover_year")
    root = font_dir()
    assert not (root / "Besley-Regular.ttf").exists()
    assert not (root / "MartianGrotesk-Regular.ttf").exists()
    assert not any(root.glob("Besley*"))
    assert not any(root.glob("Martian*"))
    assert set(jost_catalog().cuts) == {
        ("jost", "book"),
        ("jost", "medium"),
        ("jost", "bold"),
        ("jost", "heavy"),
    }


def test_unknown_family_and_weight_both_keyerror_at_catalog():
    ramp = EffectiveRamp(overlay=TypeOverlay(chrome=TypePatch(family="not-a-font", weight="book")))
    with pytest.raises(KeyError, match="family='not-a-font' weight='book'"):
        ramp.ink("chrome")


def test_compose_overlays_later_family_wins():
    device = TypeOverlay(chrome=TypePatch(family="jost", size=8.6))
    press_over = TypeOverlay(chrome=TypePatch(family="jost", size=10.0))
    merged = compose_overlays(device, press_over)
    ramp = EffectiveRamp(overlay=merged)
    assert ramp.ink("chrome") == TypeInk(family="jost", weight="book", size=10.0)
    later_family = compose_overlays(
        TypeOverlay(chrome=TypePatch(family="jost", weight="bold")),
        TypeOverlay(chrome=TypePatch(family="jost")),
    )
    assert later_family.chrome is not None
    assert later_family.chrome.family == "jost"
    assert later_family.chrome.weight == "bold"


def test_compose_overlays_missing_family_keeps_previous():
    first = TypeOverlay(cover_year=TypePatch(family="jost", size=40))
    second = TypeOverlay(cover_year=TypePatch(weight="heavy"))
    merged = compose_overlays(first, second)
    ramp = EffectiveRamp(overlay=merged)
    assert ramp.ink("cover_year") == TypeInk(family="jost", weight="heavy", size=40)


def test_empty_effective_ramp_matches_jost_defaults():
    empty = EffectiveRamp()
    jost = JostRamp()
    for role in ("cover_year", "cover_brow", "page_title", "chrome"):
        assert empty.ink(role) == jost.ink(role)


def test_jost_family_overlay_matches_jost_defaults():
    ramp = EffectiveRamp(overlay=JOST_FAMILY_OVERLAY)
    jost = JostRamp()
    for role in ("cover_year", "cover_brow", "page_title", "chrome"):
        assert ramp.ink(role) == jost.ink(role)


def test_bind_ramp_explicit_wins_over_overlay():
    class StubRamp:
        catalog = jost_catalog()

        def ink(self, role: TypeRole) -> TypeInk:
            return TypeInk(family="jost", weight="book", size=3)

    stub = StubRamp()
    bound = bind_ramp(ramp=stub, overlay=TypeOverlay(chrome=TypePatch(family="jost", size=99)))
    assert bound is stub
    assert bound.ink("chrome").size == 3
    overlay_only = bind_ramp(overlay=TypeOverlay(chrome=TypePatch(family="jost", size=9.0)))
    assert overlay_only.ink("chrome") == TypeInk(family="jost", weight="book", size=9.0)


def test_patch_validators_are_pure_and_skip_family():
    with pytest.raises(ValueError, match="size must be > 0"):
        TypePatch(size=0)
    with pytest.raises(ValueError, match="unknown weight"):
        TypePatch(weight="hairline")  # type: ignore[arg-type]
    # Unknown family is legal on the patch — catalog.path fails later.
    fake = TypePatch(family="besley")
    assert fake.family == "besley"
    assert fake.size is None
    assert fake.weight is None


def test_family_overlay_reaches_cover_and_header():
    ramp = EffectiveRamp(overlay=JOST_FAMILY_OVERLAY)
    cover = RecordingPlotter()
    paint_cover(cover, NOMAD, _cover(), ramp=ramp)
    year = next(op for op in cover.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == 42
    assert year[9] == "heavy"
    assert _family(year) == "jost"
    brow = next(op for op in cover.ops if op[0] == "text" and op[2] == "Year Book")
    assert brow[3] == 10
    assert brow[9] == "medium"
    assert _family(brow) == "jost"
    header = RecordingPlotter()
    paint_header(header, NOMAD, "Year", "2026", chip="01", ramp=ramp)
    title = next(op for op in header.ops if op[0] == "text" and op[2] == "Year")
    assert title[3] == 11
    assert title[9] == "medium"
    assert _family(title) == "jost"
    chip = next(op for op in header.ops if op[0] == "text" and op[2] == "01")
    assert chip[3] == 7.4
    assert chip[9] == "book"
    assert _family(chip) == "jost"


def test_device_family_overlay_reaches_painters_via_layout():
    layout = PlannerLayout(overlay=NOMAD.type_overlay)
    page = next(p for p in YearPlanner().pages(Spec(notes_pages=1)) if p.dest == "year-2026")
    plotter = RecordingPlotter()
    plotter.begin_page()
    layout.paint(page, plotter, NOMAD)
    meta = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Q1–Q4")
    assert _family(meta) == "jost"
    assert meta[3] == 7.4
    assert meta[9] == "book"
    title = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert title[3] == 11
    assert title[9] == "medium"
    assert _family(title) == "jost"


def test_press_builds_effective_ramp_from_device_family_overlay(tmp_path: Path):
    plotter = RecordingPlotter()
    out = tmp_path / "family-overlay.pdf"
    press(Spec(months=(1,), notes_pages=0, project_index_pages=1), out, plotter=plotter)
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year Book")
    assert _family(brow) == "jost"
    assert brow[3] == 10
    assert brow[9] == "medium"
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == 42
    assert year[9] == "heavy"
    assert _family(year) == "jost"
    device_ramp = bind_ramp(overlay=compose_overlays(NOMAD_TYPE_OVERLAY, None))
    assert device_ramp.ink("chrome") == TypeInk(family="jost", weight="book", size=7.4)
    assert device_ramp.ink("cover_year").family == "jost"


def test_press_overlay_family_can_layer_on_device(tmp_path: Path):
    plotter = RecordingPlotter()
    out = tmp_path / "layered.pdf"
    press(
        Spec(months=(1,), notes_pages=0, project_index_pages=1),
        out,
        plotter=plotter,
        overlay=TypeOverlay(cover_year=TypePatch(family="jost", size=36)),
    )
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == 36
    assert year[9] == "heavy"
    assert _family(year) == "jost"


def test_stub_ramp_still_works_on_effective_path():
    class StubRamp:
        catalog = jost_catalog()

        def ink(self, role: TypeRole) -> TypeInk:
            return TypeInk(family="jost", weight="heavy", size=14)

    layout = PlannerLayout(ramp=StubRamp())
    plotter = RecordingPlotter()
    paint_header(plotter, NOMAD, "Year", "2026", ramp=layout.ramp)
    title = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year")
    assert title[3] == 14
    assert title[9] == "heavy"
    assert _family(title) == "jost"
